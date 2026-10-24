"""Merging duplicate fact assertions into one (ADR 0063).

plan() checks that the assertions say the same thing (subject, fact type,
date, value, place) and can be joined without a human choice, chooses the
assertion to keep, joins the citations and lists every file that links to
the assertions that go away. apply() writes the plan: the kept assertion
with all citations, the links rewritten, the other files deleted (git keeps
them). Anything that needs a decision – another confidence, another
evaluation of the same citation, a confirmation on the assertion that would
go away – stops the plan; the researcher decides.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .frontmatter import join, split
from .validator import Entity, RepoValidator

# Fields of a fact assertion that must agree; lists are joined, the rest must be equal.
SAME = ("kind", "subject", "fact_type", "date", "value")
JOINED_LISTS = ("tags", "refs", "schema_gap")
SKIP = {"id", "type", "created", "created_by", "citations", "confirmed", "confidence", "place", "place_as_written"} | set(SAME) | set(JOINED_LISTS)


@dataclass
class Plan:
    keep: str | None = None
    drop: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)          # header of the kept assertion after the merge
    body: str = ""
    links: dict[str, list[str]] = field(default_factory=dict)   # file → IDs that go away
    problems: list[str] = field(default_factory=list)  # stop: a human decides
    notes: list[str] = field(default_factory=list)     # worth a look, does not stop

    @property
    def ok(self) -> bool:
        return not self.problems and self.keep is not None


def _cite_key(c: dict) -> tuple:
    """What a citation points to, without its evaluation."""
    return tuple((k, str(c.get(k))) for k in ("record", "participant", "source", "detail", "oral", "coverage") if c.get(k) is not None)


def _links(v: RepoValidator, ids: set[str]) -> dict[str, list[str]]:
    pattern = re.compile(r"\b(" + "|".join(re.escape(i) for i in sorted(ids)) + r")\b")
    out = {}
    for e in sorted(v.entities.values(), key=lambda e: str(e.path)):
        if e.id in ids:
            continue
        text = (v.root / e.path).read_text(encoding="utf-8")
        found = sorted(set(pattern.findall(text)))
        if found:
            out[e.path.as_posix()] = found
    return out


def plan(repo: Path, framework: Path, ids: list[str], keep: str | None = None, confidence: str | None = None) -> Plan:
    v = RepoValidator(repo, framework)
    v.run()
    p = Plan()
    entities: list[Entity] = []
    for i in dict.fromkeys(ids):
        e = v.entities.get(i)
        if e is None or e.type != "assertion":
            p.problems.append(f"{i} is not an assertion in this repository")
        elif e.data.get("kind") != "fact":
            p.problems.append(f"{i} is an identity link – merge persons through aliases and the identity gate, not here")
        else:
            entities.append(e)
    if len(entities) < 2:
        p.problems.append("give at least two fact assertions")
        return p

    canon = lambda x: v.aliases.get(x, x)  # noqa: E731
    first = entities[0]
    for e in entities[1:]:
        for k in SAME:
            a, b = first.data.get(k), e.data.get(k)
            if k == "subject":
                a, b = canon(a), canon(b)
            if str(a if a is not None else "") != str(b if b is not None else ""):
                p.problems.append(f"{e.id} has {k} {b!r}, {first.id} {a!r} – not the same fact")
        if not v.same_place(v.place_key(first), v.place_key(e)):
            p.problems.append(f"{e.id} and {first.id} name different places – two versions: write a conflict, do not merge")

    # Which one stays: the one named, else the one with the most links to it, else the oldest ID.
    all_ids = {e.id for e in entities}
    links = _links(v, all_ids)
    count = {e.id: sum(e.id in found for found in links.values()) for e in entities}
    if keep is not None and keep not in all_ids:
        p.problems.append(f"--keep {keep} is not one of the assertions to merge")
        return p
    kept = next(e for e in entities if e.id == keep) if keep else sorted(entities, key=lambda e: (-count[e.id], e.id))[0]
    p.keep = kept.id
    p.drop = [e.id for e in entities if e is not kept]

    confidences = {e.data.get("confidence") for e in entities}
    if confidence is None and len(confidences) > 1:
        each = ", ".join(f"{e.id}: {e.data.get('confidence')}" for e in entities)
        p.problems.append(f"the confidences differ ({each}) – the researcher chooses one: --confidence <value>")
    for e in entities:
        if e is not kept and "confirmed" in e.data and e.data.get("confirmed") != kept.data.get("confirmed"):
            p.problems.append(f"{e.id} carries a confirmation the kept {kept.id} does not – keep {e.id} (--keep {e.id}) "
                              "or let the researcher confirm again")

    data = dict(kept.data)
    cites: list[dict] = []
    seen: dict[tuple, dict] = {}
    for e in [kept] + [x for x in entities if x is not kept]:
        for c in e.data.get("citations") or []:
            if not isinstance(c, dict):
                continue
            key = _cite_key(c)
            if key in seen:
                if seen[key] != c:
                    p.problems.append(f"{e.id} evaluates the citation {dict(key)} otherwise than {kept.id} "
                                      "(information or evidence) – the researcher decides")
                continue
            seen[key] = c
            cites.append(c)
    data["citations"] = cites
    for k in JOINED_LISTS:
        values = [x for e in entities for x in e.data.get(k) or []]
        if values:
            data[k] = [x for x in dict.fromkeys(values) if x not in all_ids or x == kept.id]
    for k in ("place", "place_as_written"):
        if data.get(k) is None:
            other = next((e.data.get(k) for e in entities if e.data.get(k) is not None), None)
            if other is not None:
                data[k] = other
    for e in entities:
        for k, value in e.data.items():
            if k in SKIP:
                continue
            if k not in data:
                data[k] = value
            elif data[k] != value:
                p.problems.append(f"{e.id} has {k} {value!r}, {kept.id} {data[k]!r} – the researcher decides")
    if confidence is not None:
        data["confidence"] = confidence
    p.data = data

    body = kept.body.rstrip("\n")
    for e in entities:
        if e is not kept and e.body.strip():
            body += f"\n\n## Merged from {e.id}\n\n{e.body.strip()}"
    p.body = (body.strip("\n") + "\n") if body.strip() else "\n"

    p.links = {path: found for path, found in _links(v, set(p.drop)).items() if path != kept.path.as_posix()}
    for x in v.of_type("conflict"):
        about = set(x.data.get("about") or [])
        if len(about & all_ids) > 1:
            p.notes.append(f"{x.id} is about {', '.join(sorted(about & all_ids))} – after the merge it names only {kept.id}; "
                           "is the conflict still a conflict?")
    return p


def _replace(value, drop: set[str], keep: str):
    """Replace the IDs that go away by the kept one, and drop repeats from lists."""
    if isinstance(value, str):
        return keep if value in drop else value
    if isinstance(value, list):
        out = []
        for x in (_replace(x, drop, keep) for x in value):
            if not (isinstance(x, str) and x == keep and keep in out):
                out.append(x)
        return out
    if isinstance(value, dict):
        return {k: _replace(x, drop, keep) for k, x in value.items()}
    return value


def apply(repo: Path, framework: Path, p: Plan) -> list[str]:
    """Write a plan that is ok. Returns the files written or deleted."""
    if not p.ok:
        raise ValueError("the plan has problems – nothing written")
    v = RepoValidator(repo, framework)
    v.run()
    drop = set(p.drop)
    pattern = re.compile(r"\b(" + "|".join(re.escape(i) for i in sorted(drop)) + r")\b")
    changed = []
    kept = v.entities[p.keep]
    (repo / kept.path).write_text(join(p.data, p.body), encoding="utf-8")
    changed.append(kept.path.as_posix())
    for rel in p.links:
        path = repo / rel
        data, body = split(path.read_text(encoding="utf-8"))
        path.write_text(join(_replace(data, drop, p.keep), pattern.sub(p.keep, body)), encoding="utf-8")
        changed.append(rel)
    for i in p.drop:
        (repo / v.entities[i].path).unlink()
        changed.append(f"{v.entities[i].path.as_posix()} (deleted)")
    return changed
