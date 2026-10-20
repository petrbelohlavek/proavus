#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Generate views of a family repository (never saved in git, ADR 0019).

Usage:  uv run .proavus/tools/build_views.py [REPO_DIR] [--root P-…] [--out FILE]

Writes REPO_DIR/views/mapa.html (ADR 0027): one self-contained HTML file
without any external resources – the ancestor tree of the starting person
(`map.root` in repo.yaml, or --root) and a card for every person with names,
facts with confidence and sources, relationships with their confidence,
non-biological and unknown parents, open conflicts and open questions.
Living persons show only what rule 9 allows: name, sex, birth and
relationships; living minors without the birth date.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FRAMEWORK = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import edtf, ids  # noqa: E402
from proavuslib.frontmatter import load_yaml  # noqa: E402
from proavuslib.quay import quay_for_citation  # noqa: E402
from proavuslib.validator import BIRTH_FACTS, DEATH_FACTS, LIVING_ALLOWED_FACTS, Entity, RepoValidator  # noqa: E402

CONFIDENCE = ["proved", "probable", "possible", "not-proved", "disproved"]
# Parent–child subtypes that continue the line of ancestors; the others
# (step, adoptive, foster, guardian) are shown but not followed further.
OWN_SUBTYPES = (None, "biological", "legitimated", "presumed")
OPEN_CONFLICT = ("open", "unresolved")
OPEN_QUESTION = ("open", "in-progress")

BOX_W, BOX_H, GAP_X, GAP_Y, PAD = 210, 54, 46, 14, 8

LABELS = {
    "en": {
        "map": "family map", "root": "Starting person", "generated": "generated",
        "check_ok": "check: no errors", "check_err": "check: {n} errors – run validate.py",
        "proved": "proved", "probable": "probable", "possible": "possible",
        "not-proved": "not proved", "disproved": "disproved",
        "lines": "Lines show the confidence of the relationship",
        "nonown": "non-biological", "unknown_parent": "unknown parent", "repeat": "shown elsewhere in the tree",
        "living": "living – only name, sex, birth and relationships are shown (rule 9)",
        "minor_date": "date not shown (living minor)",
        "hidden": "details not shown (living person)",
        "names": "Names", "facts": "Facts", "identity": "In records", "parents": "Parents",
        "partners": "Partners", "children": "Children", "conflicts": "Open conflicts",
        "questions": "Open questions", "people": "People", "none": "none",
        "male": "male", "female": "female", "unknown": "sex unknown",
        "deceased": "deceased", "unknown_status": "vital status unknown",
        "candidate": "candidate", "decides": "What would decide it",
        "not_in_tree": "not in the tree", "pick": "Click a person in the tree.",
        "claimed": "claimed by", "about": "about", "from": "from", "to": "to",
        "support": "supported by", "confirmed": "confirmed", "bapt": "bapt.", "bur": "bur.",
    },
    "cs": {
        "map": "mapa rodiny", "root": "Výchozí osoba", "generated": "vygenerováno",
        "check_ok": "kontrola: bez chyb", "check_err": "kontrola: {n} chyb – spusťte validate.py",
        "proved": "prokázáno", "probable": "pravděpodobné", "possible": "možné",
        "not-proved": "neprokázáno", "disproved": "vyvráceno",
        "lines": "Čára ukazuje jistotu vztahu",
        "nonown": "nevlastní", "unknown_parent": "neznámý rodič", "repeat": "ve stromu už je jinde",
        "living": "žijící – zobrazeno jen jméno, pohlaví, narození a vztahy (pravidlo 9)",
        "minor_date": "datum neuvedeno (žijící nezletilá osoba)",
        "hidden": "podrobnosti neuvedeny (žijící osoba)",
        "names": "Jména", "facts": "Údaje", "identity": "V záznamech", "parents": "Rodiče",
        "partners": "Partneři", "children": "Děti", "conflicts": "Otevřené rozpory",
        "questions": "Otevřené otázky", "people": "Osoby", "none": "žádné",
        "male": "muž", "female": "žena", "unknown": "pohlaví neznámé",
        "deceased": "zemřelý/á", "unknown_status": "není známo, zda žije",
        "candidate": "kandidát", "decides": "Co rozhodne",
        "not_in_tree": "mimo strom", "pick": "Klikněte na osobu ve stromu.",
        "claimed": "zabral/a", "about": "týká se", "from": "od", "to": "do",
        "support": "opírá se o", "confirmed": "potvrdil/a", "bapt": "křt.", "bur": "pohř.",
    },
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


@dataclass
class Node:
    person: str | None                 # person ID, None = explicitly unknown parent
    rel: Entity | None = None          # relationship to the child (None for the root)
    depth: int = 0
    repeat: bool = False               # already shown elsewhere: not expanded again
    nonown: bool = False               # step / adoptive / foster / guardian: not expanded
    parents: list["Node"] = field(default_factory=list)
    y: float = 0.0


class MapBuilder:
    def __init__(self, repo: Path, out: Path, today: dt.date, root: str | None = None):
        self.repo = repo
        self.out = out
        self.today = today
        self.v = RepoValidator(repo, FRAMEWORK, today=today)
        self.report = self.v.run()
        config = self.v.config
        settings = config.get("map") if isinstance(config.get("map"), dict) else {}
        self.lang = settings.get("lang") if settings.get("lang") in LABELS else "en"
        self.L = LABELS[self.lang]
        self.title = config.get("title") or "Proavus"
        root = root or settings.get("root")
        if not root:
            raise SystemExit("build_views: no starting person – set map.root in repo.yaml or use --root P-…")
        self.root = self.canon(root)
        if self.root not in {e.id for e in self.v.of_type("person")}:
            raise SystemExit(f"build_views: starting person {root} not found in people/")
        self.vocab = _load_vocab()
        self._index()

    # ------------------------------------------------------------- lookups
    def canon(self, id_):
        return self.v.aliases.get(id_, id_) if isinstance(id_, str) else id_

    def get(self, id_) -> Entity | None:
        return self.v.entities.get(self.canon(id_)) if isinstance(id_, str) else None

    def label(self, vocab: str, value) -> str:
        if value is None:
            return ""
        entry = self.vocab.get(vocab, {}).get(value)
        return (entry.get(self.lang) or entry.get("en") or str(value)) if entry else str(value)

    def _index(self) -> None:
        self.people = {e.id: e for e in self.v.of_type("person")}
        self.parent_rels: dict[str, list[Entity]] = {}
        self.child_rels: dict[str, list[Entity]] = {}
        self.partner_rels: dict[str, list[Entity]] = {}
        for rel in sorted(self.v.of_type("relationship"), key=lambda r: r.id):
            parties = [p for p in rel.data.get("parties") or [] if isinstance(p, dict)]
            if rel.data.get("rel_type") == "parent-child":
                for p in parties:
                    if p.get("role") == "child":
                        self.parent_rels.setdefault(self.canon(p.get("person")), []).append(rel)
                    elif p.get("role") == "parent" and p.get("person") != "unknown":
                        self.child_rels.setdefault(self.canon(p.get("person")), []).append(rel)
            else:
                for p in parties:
                    self.partner_rels.setdefault(self.canon(p.get("person")), []).append(rel)
        self.facts: dict[str, list[Entity]] = {}
        self.identities: dict[str, list[Entity]] = {}
        for a in sorted(self.v.of_type("assertion"), key=lambda a: a.id):
            if a.data.get("kind") == "fact":
                self.facts.setdefault(self.canon(a.data.get("subject")), []).append(a)
            elif a.data.get("kind") == "identity":
                self.identities.setdefault(self.canon(a.data.get("person")), []).append(a)
        self.living = {pid for pid, p in self.people.items() if self.v.is_living(p)}
        self.minors = {pid for pid, p in self.people.items() if self.v.is_minor(p)}

    @staticmethod
    def party(rel: Entity, role: str) -> list:
        return [p.get("person") for p in rel.data.get("parties") or [] if isinstance(p, dict) and p.get("role") == role]

    def touches_living(self, ref) -> bool:
        """Is the entity (person, assertion, relationship) about a living person?"""
        ref = self.canon(ref)
        if ref in self.living:
            return True
        e = self.get(ref)
        if e is None:
            return False
        if e.type == "assertion":
            return self.canon(e.data.get("subject")) in self.living or self.canon(e.data.get("person")) in self.living
        if e.type == "relationship":
            return any(self.canon(p.get("person")) in self.living for p in e.data.get("parties") or [] if isinstance(p, dict))
        return False

    def visible_facts(self, pid: str) -> list[Entity]:
        facts = self.facts.get(pid, [])
        if pid in self.living:
            facts = [a for a in facts if a.data.get("fact_type") in LIVING_ALLOWED_FACTS]
        return sorted(facts, key=lambda a: (_start(a.data.get("date")), a.data.get("fact_type", ""), a.id))

    def best_fact(self, pid: str, types) -> Entity | None:
        found = [a for a in self.visible_facts(pid) if a.data.get("fact_type") in types and a.data.get("confidence") != "disproved"]
        found.sort(key=lambda a: (types.index(a.data["fact_type"]), _rank(a.data.get("confidence")), a.id))
        return found[0] if found else None

    def show_date(self, pid: str, fact: Entity) -> str | None:
        if pid in self.minors and fact.data.get("fact_type") in BIRTH_FACTS:
            return None
        date = fact.data.get("date")
        return None if date is None else str(date)

    def name(self, pid) -> str:
        p = self.people.get(self.canon(pid))
        if p is None:
            return str(pid)
        names = [n for n in p.data.get("names") or [] if isinstance(n, dict)]
        preferred = [n for n in names if n.get("preferred")]
        return str((preferred or names or [{"value": pid}])[0].get("value"))

    def life(self, pid: str) -> str:
        parts = []
        birth = self.best_fact(pid, BIRTH_FACTS)
        if birth is not None and self.show_date(pid, birth):
            parts.append(("*" if birth.data["fact_type"] == "birth" else self.L["bapt"]) + " " + self.show_date(pid, birth))
        death = self.best_fact(pid, DEATH_FACTS)
        if death is not None and death.data.get("date") is not None:
            parts.append(("†" if death.data["fact_type"] == "death" else self.L["bur"]) + " " + str(death.data["date"]))
        return "  ".join(parts)

    def file_href(self, entity: Entity) -> str:
        return Path(os.path.relpath(self.repo / entity.path, self.out.parent)).as_posix()

    def ref(self, id_) -> str:
        """Link to a person card, or to the file of any other entity."""
        id_ = self.canon(id_)
        if id_ in self.people:
            return f'<a href="#{esc(id_)}">{esc(self.name(id_))}</a>'
        e = self.get(id_)
        if e is None:
            return f"<code>{esc(id_)}</code>"
        return f'<a href="{esc(self.file_href(e))}"><code>{esc(id_)}</code></a>'

    # ----------------------------------------------------------------- tree
    def tree(self) -> Node:
        shown: set[str] = set()

        def build(node: Node) -> Node:
            shown.add(node.person)
            rels = [r for r in self.parent_rels.get(node.person, []) if r.data.get("confidence") != "disproved"]
            rels.sort(key=self._parent_order)
            for rel in rels:
                for parent in self.party(rel, "parent"):
                    nonown = rel.data.get("subtype") not in OWN_SUBTYPES
                    if parent == "unknown":
                        node.parents.append(Node(None, rel, node.depth + 1, nonown=nonown))
                        continue
                    parent = self.canon(parent)
                    if parent not in self.people:
                        continue
                    child = Node(parent, rel, node.depth + 1, repeat=parent in shown, nonown=nonown)
                    node.parents.append(child if child.repeat or nonown else build(child))
                    shown.add(parent)
            return node

        root = build(Node(self.root))
        slot = [0]

        def place(node: Node) -> None:
            for p in node.parents:
                place(p)
            if node.parents:
                node.y = sum(p.y for p in node.parents) / len(node.parents)
            else:
                node.y = slot[0] * (BOX_H + GAP_Y)
                slot[0] += 1

        place(root)
        return root

    def _parent_order(self, rel: Entity):
        parents = self.party(rel, "parent")
        person = self.people.get(self.canon(parents[0])) if parents else None
        sex = person.data.get("sex") if person else None
        return (rel.data.get("subtype") not in OWN_SUBTYPES, {"male": 0, "female": 1}.get(sex, 2), rel.id)

    def svg(self, root: Node) -> str:
        nodes: list[Node] = []

        def walk(n: Node):
            nodes.append(n)
            for p in n.parents:
                walk(p)

        walk(root)
        width = (max(n.depth for n in nodes) + 1) * (BOX_W + GAP_X) - GAP_X + 2 * PAD
        height = max(n.y for n in nodes) + BOX_H + 2 * PAD
        out = [f'<svg class="tree" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" role="img" aria-label="{esc(self.L["map"])}">']
        for n in nodes:
            for p in n.parents:
                x1, y1 = PAD + n.depth * (BOX_W + GAP_X) + BOX_W, PAD + n.y + BOX_H / 2
                x2, y2 = PAD + p.depth * (BOX_W + GAP_X), PAD + p.y + BOX_H / 2
                xm = x1 + GAP_X / 2
                conf = p.rel.data.get("confidence", "possible")
                cls = f"edge c-{esc(conf)}" + (" nonown" if p.nonown else "")
                out.append(f'<path class="{cls}" data-rel="{esc(p.rel.id)}" d="M{x1:.0f},{y1:.0f} H{xm:.0f} V{y2:.0f} H{x2:.0f}"><title>{esc(self._rel_title(p.rel))}</title></path>')
        for n in nodes:
            x, y = PAD + n.depth * (BOX_W + GAP_X), PAD + n.y
            if n.person is None:
                sub = self.label("relationship_subtypes", n.rel.data.get("subtype")) if n.nonown else ""
                out.append(f'<g class="node unknown" transform="translate({x:.0f},{y:.0f})"><rect width="{BOX_W}" height="{BOX_H}" rx="6"/>'
                           f'<text x="10" y="22" class="nm">? {esc(self.L["unknown_parent"])}</text>'
                           f'<text x="10" y="40" class="sub">{esc(sub)}</text></g>')
                continue
            pid = n.person
            classes = ["node"]
            if pid in self.living:
                classes.append("living")
            if n.nonown:
                classes.append("nonown")
            if n.repeat:
                classes.append("repeat")
            sub = self.life(pid)
            if n.nonown:
                sub = self.label("relationship_subtypes", n.rel.data.get("subtype")) + ("  " + sub if sub else "")
            if n.repeat:
                sub = "↺ " + self.L["repeat"]
            out.append(f'<a href="#{esc(pid)}" data-person="{esc(pid)}"><g class="{" ".join(classes)}" transform="translate({x:.0f},{y:.0f})">'
                       f'<title>{esc(self.name(pid))}</title><rect width="{BOX_W}" height="{BOX_H}" rx="6"/>'
                       f'<text x="10" y="22" class="nm">{esc(_clip(self.name(pid), 26))}</text>'
                       f'<text x="10" y="40" class="sub">{esc(_clip(sub, 32))}</text></g></a>')
        out.append("</svg>")
        return "\n".join(out)

    def _rel_title(self, rel: Entity) -> str:
        bits = [self.label("relationship_subtypes", rel.data.get("subtype")) if rel.data.get("subtype") else "",
                self.L.get(rel.data.get("confidence"), str(rel.data.get("confidence"))), rel.id]
        return " · ".join(b for b in bits if b)

    # ----------------------------------------------------------------- cards
    def conf(self, value) -> str:
        value = value if value in CONFIDENCE else "possible"
        return f'<span class="conf c-{value}"><svg width="26" height="8" aria-hidden="true"><line class="edge c-{value}" x1="1" y1="4" x2="25" y2="4"/></svg>{esc(self.L[value])}</span>'

    def citation(self, c: dict, show_participant: bool) -> str:
        parts, form, url = [], None, None
        if c.get("record"):
            rec = self.get(c["record"])
            parts.append(self.ref(c["record"]))
            if rec is not None:
                src = self.get(rec.data.get("source"))
                if src is not None:
                    parts.append(esc(src.data.get("title", "")))
                    form = src.data.get("form")
                loc = rec.data.get("locator") or {}
                where = ", ".join(f"{k} {loc[k]}" for k in ("page", "folio", "entry", "image") if loc.get(k) is not None)
                if where:
                    parts.append(esc(where))
                url = loc.get("url")
                if show_participant and c.get("participant"):
                    for p in rec.data.get("participants") or []:
                        if isinstance(p, dict) and p.get("key") == c["participant"]:
                            parts.append(f'{esc(p["key"])}: „{esc(p.get("name_as_written", ""))}“ ({esc(self.label("participant_roles", p.get("role")))})')
        elif c.get("source"):
            src = self.get(c["source"])
            parts.append(self.ref(c["source"]))
            if src is not None:
                parts.append(esc(src.data.get("title", "")))
                form, url = src.data.get("form"), src.data.get("url")
        else:
            key = next((k for k in ("oral", "coverage") if c.get(k)), None)
            if key:
                parts.append(self.ref(c[key]))
        if c.get("detail"):
            parts.append(esc(c["detail"]))
        if url and str(url).startswith(("http://", "https://")):
            parts.append(f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">↗</a>')
        quality = [x for x in (c.get("information"), c.get("evidence")) if x]
        if quality:
            q = quay_for_citation(form, c.get("information"), c.get("evidence"))
            parts.append(f'<span class="muted">{esc(" · ".join(quality))} · QUAY {q}</span>')
        return " · ".join(p for p in parts if p)

    def place_name(self, a: Entity) -> str:
        place = self.get(a.data.get("place"))
        if place is not None:
            names = place.data.get("names") or [{}]
            same = [n for n in names if isinstance(n, dict) and n.get("lang") == self.lang]
            name = (same or names)[0].get("value", place.id)
            return f'<a href="{esc(self.file_href(place))}">{esc(name)}</a>'
        return esc(a.data.get("place_as_written", ""))

    def card(self, pid: str, in_tree: bool) -> str:
        p = self.people[pid]
        L, living = self.L, pid in self.living
        badges = [esc(L.get(p.data.get("sex"), "")) if p.data.get("sex") else ""]
        status = p.data.get("vital_status")
        if living:
            badges.append(f'<span class="tag living">{esc(L["living"])}</span>')
        elif status == "deceased":
            badges.append(esc(L["deceased"]))
        elif status == "unknown":
            badges.append(esc(L["unknown_status"]))
        if p.data.get("candidate"):
            badges.append(f'<span class="tag">{esc(L["candidate"])}</span>')
        if not in_tree:
            badges.append(f'<span class="tag">{esc(L["not_in_tree"])}</span>')
        out = [f'<section class="card" id="{esc(pid)}">',
               f'<h2>{esc(self.name(pid))}</h2>',
               f'<p class="meta"><a href="{esc(self.file_href(p))}"><code>{esc(pid)}</code></a> · {" · ".join(b for b in badges if b)}</p>']

        names = [n for n in p.data.get("names") or [] if isinstance(n, dict)]
        if len(names) > 1:
            out.append(f"<h3>{esc(L['names'])}</h3><ul>")
            for n in names:
                extra = ", ".join(x for x in (self.label("name_types", n.get("name_type")), n.get("lang")) if x)
                out.append(f"<li>{esc(n.get('value'))} <span class='muted'>({esc(extra)})</span></li>")
            out.append("</ul>")

        facts = self.visible_facts(pid)
        out.append(f"<h3>{esc(L['facts'])}</h3>")
        if facts:
            out.append('<ul class="facts">')
            for a in facts:
                date = self.show_date(pid, a)
                if date is None and a.data.get("date") is not None:
                    date_html = f'<span class="muted">{esc(L["minor_date"])}</span>'
                else:
                    date_html = esc(date or "")
                what = f"<b>{esc(self.label('fact_types', a.data.get('fact_type')))}</b>"
                if a.data.get("value") is not None:
                    what += f": {esc(a.data['value'])}"
                head = " · ".join(x for x in (what, date_html, self.place_name(a), self.conf(a.data.get("confidence"))) if x)
                cites = "".join(f"<li>{self.citation(c, not living)}</li>" for c in a.data.get("citations") or [] if isinstance(c, dict))
                cls = ' class="disproved"' if a.data.get("confidence") == "disproved" else ""
                out.append(f'<li{cls}>{head} <a class="id" href="{esc(self.file_href(a))}">{esc(a.id)}</a><ul class="src">{cites}</ul></li>')
            out.append("</ul>")
        else:
            out.append(f"<p class='muted'>{esc(L['none'])}</p>")

        if not living and self.identities.get(pid):
            out.append(f"<h3>{esc(L['identity'])}</h3><ul>")
            for a in self.identities[pid]:
                part = a.data.get("participant") or {}
                cite = self.citation({"record": part.get("record"), "participant": part.get("key")}, True)
                out.append(f"<li>{cite} · {self.conf(a.data.get('confidence'))} <a class='id' href='{esc(self.file_href(a))}'>{esc(a.id)}</a></li>")
            out.append("</ul>")

        out += self._relations(pid, L["parents"], self.parent_rels.get(pid, []), "parent")
        out += self._relations(pid, L["partners"], self.partner_rels.get(pid, []), "partner")
        out += self._relations(pid, L["children"], self.child_rels.get(pid, []), "child")

        related = {pid} | {a.id for a in self.facts.get(pid, [])} | {
            r.id for rels in (self.parent_rels, self.child_rels, self.partner_rels) for r in rels.get(pid, [])}
        conflicts = [x for x in self.open_conflicts() if related & {self.canon(r) for r in x.data.get("about") or []}]
        questions = [q for q in self.open_questions() if pid in {self.canon(s) for s in q.data.get("subjects") or []}]
        if conflicts:
            out.append(f"<h3>{esc(L['conflicts'])}</h3><ul>" + "".join(f"<li>{self.conflict(x)}</li>" for x in conflicts) + "</ul>")
        if questions:
            out.append(f"<h3>{esc(L['questions'])}</h3><ul>" + "".join(f"<li>{self.question(q)}</li>" for q in questions) + "</ul>")
        out.append("</section>")
        return "\n".join(out)

    def _relations(self, pid: str, heading: str, rels: list[Entity], other_role: str) -> list[str]:
        if not rels:
            return []
        out = [f"<h3>{esc(heading)}</h3><ul>"]
        for rel in sorted(rels, key=lambda r: (r.data.get("subtype") not in OWN_SUBTYPES, _rank(r.data.get("confidence")), r.id)):
            others = [o for o in self.party(rel, other_role) if self.canon(o) != pid]
            who = ", ".join(esc(self.L["unknown_parent"]) if o == "unknown" else self.ref(o) for o in others) or "–"
            bits = [who]
            subtype = rel.data.get("subtype")
            if subtype:
                tag = "tag nonown" if rel.data.get("rel_type") == "parent-child" and subtype not in OWN_SUBTYPES else "tag"
                bits.append(f'<span class="{tag}">{esc(self.label("relationship_subtypes", subtype))}</span>')
            bits.append(self.conf(rel.data.get("confidence")))
            if not self.touches_living(rel.id):
                span = [f"{self.L[k]} {esc(rel.data[f])}" for k, f in (("from", "start"), ("to", "end")) if rel.data.get(f) is not None]
                bits += span
            support = rel.data.get("assertions") or []
            if support:
                bits.append(f'<span class="muted">{esc(self.L["support"])}</span> ' + ", ".join(self.ref(a) for a in support))
            confirmed = rel.data.get("confirmed")
            if isinstance(confirmed, dict):
                bits.append(f'<span class="muted">{esc(self.L["confirmed"])} {esc(confirmed.get("by", ""))} {esc(confirmed.get("on", ""))}</span>')
            bits.append(f'<a class="id" href="{esc(self.file_href(rel))}">{esc(rel.id)}</a>')
            cls = ' class="disproved"' if rel.data.get("confidence") == "disproved" else ""
            out.append(f"<li{cls}>{' · '.join(bits)}</li>")
        out.append("</ul>")
        return out

    # -------------------------------------------------- conflicts, questions
    def open_conflicts(self) -> list[Entity]:
        return sorted((c for c in self.v.of_type("conflict") if c.data.get("status") in OPEN_CONFLICT), key=lambda c: c.id)

    def open_questions(self) -> list[Entity]:
        return sorted((q for q in self.v.of_type("question") if q.data.get("status") in OPEN_QUESTION), key=lambda q: q.id)

    def conflict(self, x: Entity) -> str:
        head = f'<a href="{esc(self.file_href(x))}"><code>{esc(x.id)}</code></a> ({esc(x.data.get("status"))})'
        about = x.data.get("about") or []
        if any(self.touches_living(r) for r in about):
            return f'{head} <span class="muted">{esc(self.L["hidden"])}</span>'
        out = f'{head} · {esc(self.L["about"])}: ' + ", ".join(self.ref(r) for r in about)
        versions = x.data.get("versions") or []
        if versions:
            out += "<ol>" + "".join(f"<li>{esc(v)}</li>" for v in versions) + "</ol>"
        if x.data.get("decides"):
            out += ("" if versions else "<br>") + f'{esc(self.L["decides"])}: {esc(x.data["decides"])}'
        return out

    def question(self, q: Entity) -> str:
        head = f'<a href="{esc(self.file_href(q))}"><code>{esc(q.id)}</code></a> ({esc(q.data.get("status"))})'
        subjects = q.data.get("subjects") or []
        if any(self.touches_living(s) for s in subjects):
            return f'{head} <span class="muted">{esc(self.L["hidden"])}</span>'
        out = f"{head} {esc(q.data.get('title', ''))}"
        if subjects:
            out += f' · {esc(self.L["about"])}: ' + ", ".join(self.ref(s) for s in subjects)
        if q.data.get("claimed_by"):
            out += f' · <span class="muted">{esc(self.L["claimed"])} {esc(q.data["claimed_by"])}</span>'
        return out

    # ------------------------------------------------------------------ page
    def render(self) -> str:
        L = self.L
        root = self.tree()
        in_tree: set[str] = set()

        def collect(n: Node):
            if n.person:
                in_tree.add(n.person)
            for p in n.parents:
                collect(p)

        collect(root)
        check = L["check_ok"] if self.report.ok else L["check_err"].format(n=len(self.report.errors))
        legend = " ".join(self.conf(c) for c in CONFIDENCE[:4])
        people = sorted(self.people, key=lambda pid: (self.name(pid).casefold(), pid))
        cards = "\n".join(self.card(pid, pid in in_tree) for pid in people)
        conflicts = self.open_conflicts()
        questions = self.open_questions()
        index = "".join(f'<li><a href="#{esc(pid)}">{esc(self.name(pid))}</a>{"" if pid in in_tree else " <span class=muted>(" + esc(L["not_in_tree"]) + ")</span>"}</li>' for pid in people)
        return PAGE.format(
            lang=self.lang,
            title=esc(f"{self.title} – {L['map']}"),
            heading=esc(self.title),
            root_label=esc(L["root"]),
            root=self.ref(self.root),
            root_id=esc(self.root),
            generated=esc(f"{L['generated']} {self.today.isoformat()}"),
            check=esc(check),
            check_cls="ok" if self.report.ok else "bad",
            legend_label=esc(L["lines"]),
            legend=legend + f' <span class="tag nonown">{esc(L["nonown"])}</span>',
            tree=self.svg(root),
            pick=esc(L["pick"]),
            cards=cards,
            conflicts_label=esc(L["conflicts"]),
            conflicts="".join(f"<li>{self.conflict(x)}</li>" for x in conflicts) or f"<li class='muted'>{esc(L['none'])}</li>",
            questions_label=esc(L["questions"]),
            questions="".join(f"<li>{self.question(q)}</li>" for q in questions) or f"<li class='muted'>{esc(L['none'])}</li>",
            people_label=esc(L["people"]),
            index=index,
        )


def _rank(confidence) -> int:
    return CONFIDENCE.index(confidence) if confidence in CONFIDENCE else len(CONFIDENCE)


def _start(date) -> int:
    return edtf.parse(date)[0] if edtf.is_valid(date) else 99999


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _load_vocab() -> dict[str, dict[str, dict]]:
    out = {}
    for path in sorted((FRAMEWORK / "schema" / "vocab").glob("*.yaml")):
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
        out[data.get("name", path.stem)] = {v["id"]: v for v in data.get("values") or [] if isinstance(v, dict) and "id" in v}
    return out


PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<!-- GENERATED by tools/build_views.py – do not edit, not saved in git (Proavus ADR 0019, 0027) -->
<title>{title}</title>
<style>
:root {{ --bg:#fbfaf7; --fg:#1f2328; --muted:#6b6f76; --line:#9a8f80; --box:#ffffff; --border:#c9c1b4;
  --accent:#7a4b1e; --living:#2f6f5e; --nonown:#8a5a9e; --bad:#b42318; --ok:#2f6f5e; --tag:#efe9df; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#171614; --fg:#e8e4dc; --muted:#a39e95; --line:#a89c8a; --box:#23211e; --border:#4a4540;
    --accent:#e0a96d; --living:#7cc4ae; --nonown:#c9a0dc; --bad:#ff8a80; --ok:#7cc4ae; --tag:#2c2925; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }}
header, main, footer {{ padding:12px 16px; }}
header h1 {{ margin:0 0 4px; font-size:1.4rem; color:var(--accent); }}
.meta, .muted {{ color:var(--muted); }}
.ok {{ color:var(--ok); }} .bad {{ color:var(--bad); font-weight:600; }}
main {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(320px,520px); gap:16px; align-items:start; }}
@media (max-width: 900px) {{ main {{ grid-template-columns:1fr; }} }}
.treebox {{ overflow:auto; border:1px solid var(--border); border-radius:8px; background:var(--bg); max-height:80vh; }}
svg.tree {{ display:block; }}
.node rect {{ fill:var(--box); stroke:var(--border); stroke-width:1.2; }}
.node .nm {{ fill:var(--fg); font-weight:600; font-size:14px; }}
.node .sub {{ fill:var(--muted); font-size:12px; }}
.node.living rect {{ stroke:var(--living); }}
.node.nonown rect {{ stroke:var(--nonown); stroke-dasharray:5 3; }}
.node.repeat rect {{ stroke-dasharray:2 3; }}
.node.unknown rect {{ fill:none; stroke:var(--muted); stroke-dasharray:4 4; }}
.node.unknown .nm {{ fill:var(--muted); font-style:italic; font-weight:400; }}
a:hover .node rect, .node.sel rect {{ stroke:var(--accent); stroke-width:2.5; }}
.edge {{ fill:none; stroke:var(--line); stroke-width:2; }}
.edge.c-proved {{ stroke-width:2.5; }}
.edge.c-probable {{ stroke-dasharray:8 4; }}
.edge.c-possible {{ stroke-dasharray:2 4; stroke-linecap:round; }}
.edge.c-not-proved {{ stroke-dasharray:1 6; stroke-linecap:round; stroke-width:1.5; opacity:.7; }}
.edge.c-disproved {{ stroke:var(--bad); stroke-dasharray:1 3; }}
.edge.nonown {{ stroke:var(--nonown); }}
.conf {{ white-space:nowrap; }} .conf svg {{ vertical-align:middle; margin-right:4px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:4px 14px; align-items:center; margin-top:6px; font-size:.9rem; }}
.tag {{ display:inline-block; padding:0 6px; border-radius:4px; background:var(--tag); font-size:.85rem; }}
.tag.living {{ color:var(--living); }} .tag.nonown {{ color:var(--nonown); }}
.card {{ display:none; border:1px solid var(--border); border-radius:8px; padding:4px 14px 12px; background:var(--box); }}
.card:target {{ display:block; }}
.card h2 {{ margin:8px 0 2px; font-size:1.25rem; }}
.card h3 {{ margin:14px 0 4px; font-size:1rem; color:var(--accent); }}
.card ul {{ padding-left:18px; margin:4px 0; }}
.cards {{ overflow-wrap:break-word; min-width:0; }}
.facts {{ list-style:none; padding-left:0 !important; }} .facts > li {{ margin-bottom:8px; }}
.src {{ font-size:.88rem; margin-top:2px !important; }}
.disproved, .disproved a {{ text-decoration:line-through; color:var(--muted); }}
a {{ color:var(--accent); }} a.id {{ font-size:.75rem; color:var(--muted); }}
code {{ font-size:.85em; }}
#hint {{ color:var(--muted); }}
footer section {{ margin-bottom:12px; }} footer h2 {{ font-size:1.1rem; color:var(--accent); }}
.index {{ columns:16em; padding-left:18px; }}
</style>
</head>
<body>
<header>
<h1>{heading}</h1>
<div class="meta">{root_label}: {root} · {generated} · <span class="{check_cls}">{check}</span></div>
<div class="legend"><span class="muted">{legend_label}:</span> {legend}</div>
</header>
<main>
<div class="treebox">
{tree}
</div>
<div class="cards">
<p id="hint">{pick}</p>
{cards}
</div>
</main>
<footer>
<section><h2>{conflicts_label}</h2><ul>{conflicts}</ul></section>
<section><h2>{questions_label}</h2><ul>{questions}</ul></section>
<section><h2>{people_label}</h2><ul class="index">{index}</ul></section>
</footer>
<script>
(function () {{
  function show() {{
    var id = decodeURIComponent(location.hash.slice(1));
    var card = id && document.getElementById(id);
    document.getElementById("hint").style.display = card ? "none" : "";
    document.querySelectorAll(".node.sel").forEach(function (n) {{ n.classList.remove("sel"); }});
    document.querySelectorAll('a[data-person="' + id + '"] .node').forEach(function (n) {{ n.classList.add("sel"); }});
  }}
  if (!location.hash) {{ history.replaceState(null, "", "#{root_id}"); }}
  window.addEventListener("hashchange", show);
  show();
}})();
</script>
</body>
</html>
"""


def build_map(repo: Path, out: Path | None = None, root: str | None = None, today: dt.date | None = None) -> tuple[Path, MapBuilder]:
    repo = repo.resolve()
    out = (out or repo / "views" / "mapa.html").resolve()
    builder = MapBuilder(repo, out, today or dt.date.today(), root)
    page = builder.render()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out, builder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate views of a Proavus family repository.")
    parser.add_argument("repo", nargs="?", default=".", help="family repository (default: .)")
    parser.add_argument("--root", help="starting person ID (default: map.root in repo.yaml)")
    parser.add_argument("--out", help="output file (default: REPO/views/mapa.html)")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.root and not ids.parse(args.root):
        raise SystemExit(f"build_views: {args.root!r} is not a person ID")
    out, builder = build_map(repo, Path(args.out).resolve() if args.out else None, args.root)
    errors = len(builder.report.errors)
    print(f"{out} written: {len(builder.people)} persons, root {builder.root}"
          + (f" – {errors} validation errors, the map may be incomplete" if errors else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
