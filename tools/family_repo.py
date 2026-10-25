#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Deterministic parts of /proavus:init, /start and /end for a family repository.

Usage:
  family_repo.py init DIR --title T --member ab:"Name" [--member …] [--region cz]
      create a new family repository from templates/family/ and install .proavus/
  family_repo.py install-tools DIR
      (re)install the pinned copy of tools, schema and method in DIR/.proavus/
  family_repo.py protect-plugin DIR [--also PATH …]
      deny Claude Code's file-editing tools in the framework (this plugin's
      folder, and PATH) via DIR/.claude/settings.local.json
  family_repo.py start-here DIR
      generate DIR/START-HERE.md (not saved in git) and print a short summary
  family_repo.py upgrade-plan DIR
      compare .proavus/VERSION with the plugin: changes (CHANGELOG), schema
      changes, migration, missing map settings with candidate starting persons
      exit 0 = upgrade available · 1 = already current · 3 = cannot upgrade
  family_repo.py upgrade DIR [--map-root P-…] [--map-lang cs|en]
      reinstall .proavus/, refresh the proavus blocks and the workflow, run a
      migration if the major version changes, set schema_version (and map),
      validate; prints the commit message · exit 1 = validation errors
  family_repo.py check-private DIR
      check that the repository's origin is private and not a fork of proavus
      exit 0 = private · 3 = public or a fork (do not write) · 4 = cannot tell
      · 5 = no remote yet
  family_repo.py hooks DIR
      switch on the pre-commit hook of the family repository (validation
      before every commit): core.hooksPath = .githooks, hook executable
  family_repo.py access DIR|OWNER/NAME
      before cloning or saving: is the repository private, and may this GitHub
      account save to it directly or only through a pull request
      exit 0 = private, save directly (admin or maintain) · 2 = private, save
      through a pull request (write) · 6 = private, read only · 3 = public or
      a fork (do not write) · 4 = cannot tell · 7 = not found or no access
  family_repo.py add-member DIR --abbr xy --name "Full name" [--role researcher]
      add a member to repo.yaml, keeping the rest of the file as written
      exit 0 = added · 1 = already listed (nothing changed)

The agent does git and GitHub steps itself, with the user's consent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FRAMEWORK = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import migrate  # noqa: E402
from proavuslib import ids, versions  # noqa: E402
from proavuslib.frontmatter import load_yaml  # noqa: E402
from proavuslib.labels import Labeler  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402

TEMPLATE = FRAMEWORK / "templates" / "family"
# An existing empty repository may contain only these (a clone, plus the
# per-machine settings Claude Code may create when the folder is opened).
EMPTY_REPO_ENTRIES = {".git", ".claude"}
# What goes into .proavus/ (ADR 0014). guard_names.py is framework-only.
COPY_DIRS = ["schema"]
COPY_TOOLS = ["validate.py", "new_id.py", "family_repo.py", "build_views.py", "migrate.py", "archive_fetch.py", "bulk_import.py", "locate.py", "merge_assertions.py", "access.py"]
COPY_METHOD = ["rules.md", "rules.cs.md", "reading-records.md"]

PROAVUS_README = """# .proavus – pinned copy of the Proavus framework

Do not edit. Version: see `VERSION`. Replaced only by `/proavus:upgrade`
(type it in a Claude Code session in this repository when `/proavus:start`
says the copy is older than the plugin). Lets every member and the GitHub check run the same tools without access to
the framework repository (Proavus ADR 0014).

From Proavus (https://github.com/petrbelohlavek/proavus), © 2026 Petr Bělohlávek
and Proavus contributors: `tools/` under MIT, `schema/` and
`regions/*/schema-ext.yaml` under CC0 1.0, `method/` under CC BY 4.0.
"""


def framework_version() -> str:
    data = json.loads((FRAMEWORK / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return data["version"]


def installed_version(repo: Path) -> str | None:
    path = repo / ".proavus" / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else None


# ---------------------------------------------------------------- install
def check_family_repo(repo: Path, cmd: str) -> None:
    """Refuse the framework itself and folders that are not family repositories."""
    if (repo / ".claude-plugin" / "marketplace.json").is_file():
        raise SystemExit(f"{cmd}: {repo} is the Proavus framework, not a family repository – run it in the family repository's folder")
    if not (repo / "repo.yaml").is_file():
        raise SystemExit(f"{cmd}: {repo} has no repo.yaml – not a Proavus family repository (create one with /proavus:init)")


def install_tools(repo: Path) -> None:
    check_family_repo(repo, "install-tools")
    target = repo / ".proavus"
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    (target / "tools").mkdir(parents=True)
    for name in COPY_TOOLS:
        shutil.copy2(TOOLS_DIR / name, target / "tools" / name)
    shutil.copytree(TOOLS_DIR / "proavuslib", target / "tools" / "proavuslib", ignore=ignore)
    for name in COPY_DIRS:
        shutil.copytree(FRAMEWORK / name, target / name, ignore=ignore)
    for ext in sorted([*(FRAMEWORK / "regions").glob("*/schema-ext.yaml"), *(FRAMEWORK / "regions").glob("*/portals.yaml"),
                       *(FRAMEWORK / "regions").glob("*/access.yaml")]):
        dest = target / "regions" / ext.parent.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ext, dest / ext.name)
    (target / "method").mkdir()
    for name in COPY_METHOD:
        shutil.copy2(FRAMEWORK / "method" / name, target / "method" / name)
    # The copy needs the plugin manifest for its version, and family_repo.py
    # looks for templates only in the framework itself.
    (target / ".claude-plugin").mkdir()
    shutil.copy2(FRAMEWORK / ".claude-plugin" / "plugin.json", target / ".claude-plugin" / "plugin.json")
    (target / "VERSION").write_text(framework_version() + "\n", encoding="utf-8")
    (target / "README.md").write_text(PROAVUS_README, encoding="utf-8")


# ------------------------------------------------------------------- init
def yaml_str(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)  # JSON strings are valid YAML


def init(repo: Path, title: str, members: list[str], regions: list[str]) -> None:
    if repo.exists():
        extra = [p.name for p in repo.iterdir() if p.name not in EMPTY_REPO_ENTRIES or (p.name == ".claude" and not p.is_dir())]
        if extra:
            raise SystemExit(f"init: {repo} is not empty ({', '.join(sorted(extra))}) – refusing to overwrite")
    if not TEMPLATE.is_dir():
        raise SystemExit("init: templates/family/ not found (run from the framework, not from .proavus)")
    parsed = []
    for m in members:
        abbr, _, name = m.partition(":")
        if not re.fullmatch(r"[a-z]{2,4}", abbr) or not name.strip():
            raise SystemExit(f"init: member must be abbr:Name with a 2–4 letter lowercase abbreviation, got {m!r}")
        parsed.append((abbr, name.strip()))
    if not parsed:
        raise SystemExit("init: at least one --member is required")
    known_ext = {p.parent.name for p in (FRAMEWORK / "regions").glob("*/schema-ext.yaml")}
    extensions = [r for r in regions if r in known_ext]

    shutil.copytree(TEMPLATE, repo, dirs_exist_ok=True)
    values = {
        "{{TITLE}}": title,
        "{{VERSION}}": framework_version(),
    }
    for path in [repo / "README.md", repo / "repo.yaml"]:
        text = path.read_text(encoding="utf-8")
        if path.name == "repo.yaml":
            text = text.replace('"{{TITLE}}"', yaml_str(title))
            text = text.replace("{{REGIONS}}", json.dumps(regions))
            text = text.replace("{{EXTENSIONS}}", json.dumps(extensions))
            text = text.replace(
                "{{MEMBERS}}",
                "\n".join(f"  - abbr: {a}\n    name: {yaml_str(n)}\n    role: researcher" for a, n in parsed),
            )
        for key, value in values.items():
            text = text.replace(key, value)
        path.write_text(text, encoding="utf-8")
    install_tools(repo)


# --------------------------------------------------------- protect-plugin
def edit_deny_rule(path: Path) -> str:
    """Claude Code rule denying all file-editing tools under an absolute path.

    `//` marks an absolute path; an Edit rule covers Edit, Write and the other
    editing tools (a Write(path) rule is not matched by file checks).
    """
    return f"Edit(/{path.resolve().as_posix()}/**)"


def protect_plugin(repo: Path, also: list[Path] | None = None) -> list[str]:
    """Add deny rules for the framework folder(s) to .claude/settings.local.json."""
    check_family_repo(repo, "protect-plugin")
    rules = [edit_deny_rule(FRAMEWORK)] + [edit_deny_rule(p) for p in also or []]
    path = repo / ".claude" / "settings.local.json"
    settings = {}
    if path.is_file():
        try:
            settings = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"protect-plugin: {path} is not valid JSON ({exc}) – fix it first, nothing was changed")
        if not isinstance(settings, dict):
            raise SystemExit(f"protect-plugin: {path} must be a JSON object – nothing was changed")
    permissions = settings.setdefault("permissions", {})
    deny = permissions.setdefault("deny", [])
    added = [r for r in dict.fromkeys(rules) if r not in deny]
    deny.extend(added)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


# ------------------------------------------------------------- START-HERE
def _session_key(s):
    return (str(s.data.get("date", "")), s.id)


def open_task_items(sessions) -> list[tuple[str, dict]]:
    """Open human tasks (ADR 0037, 0039): (session ID, task as {task, status, …}).

    Tasks with a state: the open ones from all sessions. Plain-text tasks cannot
    be closed, so only those of the latest session count.
    """
    sessions = sorted(sessions, key=_session_key)
    latest = sessions[-1].id if sessions else None
    out = []
    for s in sessions:
        for task in s.data.get("human_tasks") or []:
            if isinstance(task, str) and s.id == latest:
                out.append((s.id, {"task": task, "status": "open"}))
            elif isinstance(task, dict) and task.get("status") == "open":
                out.append((s.id, task))
    return out


def open_tasks(sessions) -> list[tuple[str, str, str | None]]:
    """Open human tasks as (session ID, task, for whom) – the short form of the map."""
    return [(sid, str(t.get("task", "")), t.get("for")) for sid, t in open_task_items(sessions)]


def task_line(lab: Labeler, task: dict) -> str:
    """A task in words, with whom it is for and the conflict or inquiry it serves (ADR 0047)."""
    text = str(task.get("task", "")) + (f" ({task['for']})" if task.get("for") else "")
    return text + "".join(f" – {lab.ref(task[k])}" for k in ("conflict", "inquiry") if task.get(k))


def waiting_inquiries(inquiries) -> list:
    """Inquiries not closed yet (ADR 0036), oldest first."""
    return sorted((i for i in inquiries if i.data.get("status") != "closed"), key=lambda i: (str(i.data.get("sent", "")), i.id))


def inquiry_state(i) -> str:
    status, sent = i.data.get("status"), i.data.get("sent")
    return f"sent {sent}" if status == "sent" else f"{status} (sent {sent})"


def _related(v: RepoValidator, person_ids: set[str]) -> set[str]:
    """The persons and the assertions and relationships about them."""
    out = set(person_ids)
    for a in v.of_type("assertion"):
        if v.aliases.get(a.data.get("subject"), a.data.get("subject")) in person_ids or a.data.get("person") in person_ids:
            out.add(a.id)
    for rel in v.of_type("relationship"):
        if any(p.get("person") in person_ids for p in rel.data.get("parties") or [] if isinstance(p, dict)):
            out.add(rel.id)
    return out


def _worked_on(v: RepoValidator, s, q, searches: list, records: set[str]) -> bool:
    """Did session s really work on question q (ADR 0047)? It lists q and q is its only
    question, or it made a search for q, holds one of q's records, sent an inquiry
    about q or gave a human task for q."""
    asked = [x for x in s.data.get("questions") or [] if isinstance(x, str)]
    if q.id not in asked:
        return False
    if len(asked) == 1:
        return True
    d = s.data
    if {c.id for c in searches} & set(d.get("coverage") or []) or records & set(d.get("records") or []):
        return True
    for i in d.get("inquiries") or []:
        inquiry = v.entities.get(v.aliases.get(i, i)) if isinstance(i, str) else None
        if inquiry is not None and q.id in (inquiry.data.get("questions") or []):
            return True
    return any(isinstance(t, dict) and t.get("question") == q.id for t in d.get("human_tasks") or [])


def question_summary(v: RepoValidator, lab: Labeler, q, tasks: list[dict] | None = None) -> list[str]:
    """What is known and open about one research question (ADR 0039)."""
    d = q.data
    head = f"### {d.get('title', q.id)} ({q.id})"
    lines = [head, "", f"- status: {d.get('status')}" + (f", claimed by {d['claimed_by']}" if d.get("claimed_by") else "")]
    subjects = [s for s in d.get("subjects") or [] if isinstance(s, str)]
    if subjects:
        lines.append("- about: " + ", ".join(lab.ref(s) for s in subjects))
    searches = [c for c in v.of_type("coverage") if q.id in (c.data.get("questions") or [])]
    if searches:
        results: dict[str, int] = {}
        for c in searches:
            results[c.data.get("result", "?")] = results.get(c.data.get("result", "?"), 0) + 1
        last = max(str(c.data.get("on", "")) for c in searches)
        lines.append(f"- searched: {len(searches)} times ({', '.join(f'{n} {r}' for r, n in sorted(results.items()))}), last {last}")
    records = list(dict.fromkeys(([d["anchor"]] if d.get("anchor") else [])
                                 + [r for c in searches for r in c.data.get("found") or []]))
    if records:
        lines.append("- records: " + "; ".join(lab.ref(r) for r in records))
    sessions = sorted((s for s in v.of_type("session") if _worked_on(v, s, q, searches, set(records))), key=_session_key)
    if sessions:
        s = sessions[-1]
        lines.append(f"- last session {s.data.get('date')} ({s.data.get('by')}): next step – {s.data.get('next_step', '')}")
    related = _related(v, set(subjects))
    conflicts = [x for x in v.of_type("conflict") if x.data.get("status") in ("open", "unresolved")
                 and related & set(x.data.get("about") or [])]
    for x in conflicts:
        lines.append(f"- open conflict: {lab.ref(x)}")
    for i in waiting_inquiries(v.of_type("inquiry")):
        if q.id in (i.data.get("questions") or []):
            lines.append(f"- inquiry: {lab.ref(i)} – {inquiry_state(i)}")
    for task in tasks or []:
        lines.append(f"- open task: {task_line(lab, task)}")
    leads = [x for x in d.get("leads") or [] if isinstance(x, dict) and x.get("status") == "open"]
    if leads:
        lines.append(f"- open leads (entries not yet shown to belong, ADR 0067): {len(leads)}")
        lines += [f"  - {x.get('where')} – {x.get('why')} ({x.get('by')}, {x.get('on')})"
                  + (f" {x['url']}" if x.get("url") else "") for x in leads]
    next_sources = (d.get("plan") or {}).get("next_sources") or []
    if next_sources:
        lines.append("- planned sources: " + "; ".join(str(x) for x in next_sources))
    return lines + [""]


def loose_task(lab: Labeler, sid: str, task: dict) -> str:
    """A task not listed under an open question: with its session, and the question
    it names if that one is no longer open."""
    q = lab.get(task.get("question"))
    where = f" – for {lab.ref(q)}, {q.data.get('status')}" if q is not None else ""
    return f"{task_line(lab, task)}{where} – {sid}"


def inaccessible_item(v, lab, cov, today: dt.date) -> str:
    """An inaccessible search with its legal time limit, if the region has one (ADR 0064)."""
    text = lab.ref(cov)
    found = v.access_limit(cov)
    if found is not None:
        lim, opens = found
        if opens <= today.year:
            text += f" – time limit passed in {opens} ({lim.years} years for {lim.kind} entries): search again"
        else:
            text += f" – open to anyone from {opens} ({lim.years} years for {lim.kind} entries)"
    if cov.data.get("access_note"):
        text += f" – {cov.data['access_note']}"
    return text


def pointer_target(lab, to) -> str:
    """Where an index pointer leads, in words: the book and the place in it (ADR 0060)."""
    to = to if isinstance(to, dict) else {}
    where = ", ".join(f"{k} {to[k]}" for k in ("volume", "page", "folio", "entry", "image") if to.get(k) is not None)
    book = lab.ref(to["source"]) if to.get("source") else "?"
    return f"{book}, {where}" if where else book


def start_here(repo: Path, today: dt.date | None = None) -> tuple[str, int]:
    today = today or dt.date.today()
    v = RepoValidator(repo, FRAMEWORK, today=today)
    report = v.run()
    of = v.of_type
    lab = Labeler(v, FRAMEWORK)
    lines = [
        "<!-- GENERATED by /start – do not edit, not saved in git -->",
        f"# START HERE – {today.isoformat()}",
        "",
    ]
    installed = installed_version(repo)
    current = framework_version()
    if installed and installed != current:
        if versions.parse(installed) > versions.parse(current):
            hint = ("the plugin is older – update it before working (Proavus TECHNICAL.md, \"Update to a new release\": "
                    "git pull on stable, then reinstall the plugin)")
        else:
            hint = "the Proavus copy is older than the plugin – run `/proavus:upgrade`"
        lines += [f"> Proavus in this repository: {installed}, plugin: {current} – {hint}.", ""]

    status = "OK" if report.ok else f"{len(report.errors)} ERRORS – fix before saving"
    lines += [f"**Check:** {status} · {report.files} files · {len(report.warnings)} warnings · {len(report.notes)} schema gaps", ""]
    for kind, messages in (("ERROR", report.errors), ("WARN", report.warnings)):
        for msg in messages[:10]:
            lines.append(f"- {kind} {msg}")
        if len(messages) > 10:
            lines.append(f"- … and {len(messages) - 10} more (`uv run .proavus/tools/validate.py .`)")
    if report.errors or report.warnings:
        lines.append("")

    open_q = sorted((q for q in of("question") if q.data.get("status") in ("open", "in-progress")), key=lambda q: q.id)
    # Each open task once (ADR 0047): under the open question it serves, the others in their own block.
    tasks = open_task_items(of("session"))
    by_question: dict[str, list[dict]] = {q.id: [] for q in open_q}
    loose = []
    for sid, task in tasks:
        qid = v.aliases.get(task.get("question"), task.get("question"))
        if qid in by_question:
            by_question[qid].append(task)
        else:
            loose.append((sid, task))
    lines += ["## Open questions", ""]
    if open_q:
        for q in open_q:
            lines += question_summary(v, lab, q, by_question[q.id])
    else:
        lines += ["No open questions yet – start by writing one.", ""]

    sessions = sorted(of("session"), key=_session_key, reverse=True)[:5]
    lines += ["## Last sessions and next steps", ""]
    if sessions:
        for s in sessions:
            about = ", ".join(lab.label(x) for x in s.data.get("questions") or [])
            lines.append(f"- **{s.data.get('date')}** ({s.data.get('by')}) {s.id}" + (f" – {about}" if about else "")
                         + f": {s.data.get('next_step', '')}")
    else:
        lines.append("No sessions yet.")
    lines.append("")

    read_once = [r for r in of("record") if (r.data.get("reading") or {}).get("status") == "read-once"]
    disputed = [r for r in of("record") if (r.data.get("reading") or {}).get("status") == "disputed"]
    conflicts = [c for c in of("conflict") if c.data.get("status") in ("open", "unresolved")]
    inquiries = waiting_inquiries(of("inquiry"))
    closed = [inaccessible_item(v, lab, cov, today) for cov in sorted(of("coverage"), key=lambda c: c.id)
              if cov.data.get("result") == "inaccessible"]
    pointers = [f"{lab.ref(cov)}: {ptr.get('name_as_written')} → {pointer_target(lab, ptr.get('to'))}" for cov, ptr in v.open_pointers()]
    lines += ["## Waiting for a human", ""]
    for title, items in (("records read once (second reading needed before identity)", [lab.ref(r) for r in read_once]),
                         ("disputed readings", [lab.ref(r) for r in disputed]),
                         ("open conflicts", [lab.ref(c) for c in conflicts]),
                         ("open human tasks without an open question", [loose_task(lab, sid, task) for sid, task in loose]),
                         ("inquiries not closed", [f"{lab.ref(i)} – {inquiry_state(i)}" for i in inquiries]),
                         ("index pointers not followed into the book yet", pointers),
                         ("searches not accessible", closed)):
        lines.append(f"- {title}: {len(items)}")
        lines += [f"  - {item}" for item in items[:10]]
        if len(items) > 10:
            lines.append(f"  - … and {len(items) - 10} more")
    under = len(tasks) - len(loose)
    if under:
        lines.append(f"- open human tasks under their questions above: {under}")
    lines.append("")

    counts = {t: len(of(t)) for t in ("person", "record", "assertion", "relationship", "coverage", "source")}
    lines += ["## Size", "", " · ".join(f"{n} {t}" for t, n in counts.items()), ""]

    (repo / "START-HERE.md").write_text("\n".join(lines), encoding="utf-8")
    summary = f"START-HERE.md written: {len(open_q)} open questions, {len(read_once)} records read once, check {status}"
    return summary, 0 if report.ok else 1


# ---------------------------------------------------------------- upgrade
# Files of the framework inside a family repository (ADR 0009). Everything
# else – the family part of CLAUDE.md and AGENTS.md, README, data – is the
# family's and never changed.
BLOCK = re.compile(r"<!-- proavus:begin -->.*?<!-- proavus:end -->", re.S)
BLOCK_FILES = ["CLAUDE.md", "AGENTS.md"]
WORKFLOW = Path(".github") / "workflows" / "validate.yml"
HOOK = Path(".githooks") / "pre-commit"   # validation before every commit (ADR 0049)
MAP_SINCE = (0, 2, 0)  # map.root and map.lang exist since 0.2.0 (ADR 0027)
MAP_LANGS = ("en", "cs")


@dataclass
class UpgradePlan:
    installed: str | None
    current: str
    status: str                      # upgrade · current · newer · migration-missing
    changelog: list[tuple[str, str]] = field(default_factory=list)
    schema: list[str] = field(default_factory=list)
    migration: bool = False
    message: str = ""
    map_missing: list[str] = field(default_factory=list)
    candidates: list[tuple[str, str]] = field(default_factory=list)
    marital: list[tuple[str, str, str]] = field(default_factory=list)
    volumes: list[tuple[str, str]] = field(default_factory=list)
    unexplained: list[str] = field(default_factory=list)


@dataclass
class UpgradeResult:
    old: str | None
    new: str
    changed: list[str]
    warnings: list[str]
    report: object

    @property
    def commit_message(self) -> str:
        return f"Upgrade Proavus {self.old or 'none'} → {self.new}"


def changelog_between(old: str | None, new: str) -> list[tuple[str, str]]:
    """CHANGELOG sections newer than old, up to and including new."""
    path = FRAMEWORK / "CHANGELOG.md"
    if not path.is_file():
        return []
    out = []
    for section in re.split(r"(?m)^## ", path.read_text(encoding="utf-8"))[1:]:
        head, _, body = section.partition("\n")
        m = re.match(r"([0-9]+\.[0-9]+\.[0-9]+)", head)
        if not m:
            continue
        v = versions.parse(m[1])
        if (old is None or v > versions.parse(old)) and v <= versions.parse(new):
            out.append((head.strip(), body.strip()))
    return out


def _properties(schema, prefix: str = "") -> set[str]:
    out: set[str] = set()
    if not isinstance(schema, dict):
        return out
    for key, value in (schema.get("properties") or {}).items():
        out.add(prefix + key)
        out |= _properties(value, prefix + key + ".")
    for part in schema.get("allOf") or []:
        out |= _properties(part, prefix)
    return out


def _schema_files(root: Path) -> set[str]:
    files = {p.relative_to(root).as_posix() for p in (root / "schema").rglob("*") if p.suffix in (".json", ".yaml")}
    return files | {p.relative_to(root).as_posix() for p in (root / "regions").glob("*/schema-ext.yaml")}


def _describe(rel: str, old: Path, new: Path) -> str:
    try:
        if rel.endswith(".json"):
            a, b = (_properties(json.loads(p.read_text(encoding="utf-8"))) for p in (old, new))
        elif rel.startswith("schema/vocab/"):
            a, b = ({v.get("id") for v in (load_yaml(p.read_text(encoding="utf-8")) or {}).get("values") or [] if isinstance(v, dict)}
                    for p in (old, new))
        else:
            return "changed"
    except (ValueError, OSError):
        return "changed"
    diff = [f"+ {x}" for x in sorted(b - a)] + [f"- {x}" for x in sorted(a - b)]
    return ", ".join(diff) if diff else "changed (no new or removed fields)"


def schema_changes(repo: Path) -> list[str]:
    """What changes between the installed .proavus/ schema and the plugin's."""
    old_root = repo / ".proavus"
    if not (old_root / "schema").is_dir():
        return ["no schema installed yet – everything is new"]
    old, new = _schema_files(old_root), _schema_files(FRAMEWORK)
    out = []
    for rel in sorted(old | new):
        a, b = old_root / rel, FRAMEWORK / rel
        if rel not in old:
            out.append(f"{rel}: new")
        elif rel not in new:
            out.append(f"{rel}: removed")
        elif a.read_bytes() != b.read_bytes():
            out.append(f"{rel}: {_describe(rel, a, b)}")
    return out


def _repo_config(repo: Path) -> dict:
    data = load_yaml((repo / "repo.yaml").read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def map_candidates(repo: Path) -> list[tuple[str, str]]:
    """Persons who are nobody's parent – the youngest generation, the usual starting persons."""
    v = RepoValidator(repo, FRAMEWORK)
    v.run()
    parents = set()
    for rel in v.of_type("relationship"):
        if rel.data.get("rel_type") == "parent-child":
            parents |= {p.get("person") for p in rel.data.get("parties") or [] if isinstance(p, dict) and p.get("role") == "parent"}
    out = []
    for person in v.of_type("person"):
        if person.id in parents:
            continue
        names = [n for n in person.data.get("names") or [] if isinstance(n, dict)]
        names.sort(key=lambda n: not n.get("preferred"))
        out.append((person.id, str(names[0].get("value")) if names else ""))
    return sorted(out, key=lambda x: (x[1].casefold(), x[0]))


# Words of a marital status in status_as_written (cs, de, la), without diacritics (ADR 0046).
MARITAL_WORDS = ("svobodn", "zenat", "vdan", "vdov", "ovdovel", "rozveden", "ledig", "verheirat", "verwitwet",
                 "witwe", "witwer", "geschieden", "coelebs", "caelebs", "vidua", "viduus", "uxorat", "nupta",
                 "conjugat", "solutus", "soluta")


def marital_hints(repo: Path) -> list[tuple[str, str, str]]:
    """Participants whose status_as_written seems to hold a marital status: (record ID, key, value)."""
    v = RepoValidator(repo, FRAMEWORK)
    v.run()
    out = []
    for rec in sorted(v.of_type("record"), key=lambda r: r.id):
        for p in rec.data.get("participants") or []:
            value = p.get("status_as_written") if isinstance(p, dict) else None
            if not isinstance(value, str) or p.get("marital_status_as_written"):
                continue
            plain = RepoValidator._name_key(value)
            if any(w in plain for w in MARITAL_WORDS):
                out.append((rec.id, str(p.get("key")), value))
    return out


# A volume written into locator.page (before 0.7.0 the locator had no volume, ADR 0058):
# a roman numeral, or tom / tomus / Bd / Band / sv. / svazek / vol.
VOLUME_IN_PAGE = re.compile(r"(?i)(^|[\s,;/])(tom(us)?|bd|band|sv|svazek|vol(ume)?)\b\.?|^\s*[IVXLC]+\b")


def volume_hints(repo: Path) -> list[tuple[str, str]]:
    """Records whose locator.page seems to hold a volume: (record ID, page)."""
    v = RepoValidator(repo, FRAMEWORK)
    v.run()
    out = []
    for rec in sorted(v.of_type("record"), key=lambda r: r.id):
        loc = rec.data.get("locator") if isinstance(rec.data.get("locator"), dict) else {}
        page = loc.get("page")
        if isinstance(page, str) and loc.get("volume") is None and VOLUME_IN_PAGE.search(page):
            out.append((rec.id, page))
    return out


def unexplained_confirmations(repo: Path) -> list[str]:
    """Records with a confirmed reading that does not say how it was confirmed (ADR 0059)."""
    v = RepoValidator(repo, FRAMEWORK)
    v.run()
    out = []
    for rec in sorted(v.of_type("record"), key=lambda r: r.id):
        reading = rec.data.get("reading") if isinstance(rec.data.get("reading"), dict) else {}
        if isinstance(reading.get("confirmed"), dict) and not reading["confirmed"].get("basis"):
            out.append(rec.id)
    return out


def plan_upgrade(repo: Path, target: str | None = None) -> UpgradePlan:
    check_family_repo(repo, "upgrade")
    installed = installed_version(repo)
    current = target or framework_version()
    plan = UpgradePlan(installed, current, "upgrade")
    if installed is not None:
        if versions.parse(installed) > versions.parse(current):
            plan.status = "newer"
            plan.message = f"this repository uses Proavus {installed}, newer than the plugin {current} – update the plugin, never downgrade"
            return plan
        if versions.parse(installed) == versions.parse(current):
            plan.status = "current"
        plan.migration = migrate.needed(installed, current)
        if plan.migration:
            try:
                migrate.steps(installed, current)
            except migrate.MigrationMissing as exc:
                plan.status = "migration-missing"
                plan.message = str(exc)
    plan.changelog = changelog_between(installed, current)
    plan.schema = schema_changes(repo)
    settings = _repo_config(repo).get("map")
    settings = settings if isinstance(settings, dict) else {}
    if versions.parse(current) >= MAP_SINCE:
        plan.map_missing = [k for k in ("root", "lang") if k not in settings]
    if "root" in plan.map_missing:
        plan.candidates = map_candidates(repo)
    plan.marital = marital_hints(repo)
    plan.volumes = volume_hints(repo)
    plan.unexplained = unexplained_confirmations(repo)
    return plan


def set_schema_version(text: str, version: str) -> str:
    line = f'schema_version: "{version}"'
    if re.search(r"(?m)^schema_version:.*$", text):
        return re.sub(r"(?m)^schema_version:.*$", line, text, count=1)
    return line + "\n" + text


def set_map(text: str, root: str | None, lang: str | None) -> str:
    """Add or change map.root / map.lang in repo.yaml, keeping everything else as written."""
    if root is not None and (not ids.parse(root) or not root.startswith("P-")):
        raise SystemExit(f"upgrade: --map-root {root!r} is not a person ID")
    if lang is not None and lang not in MAP_LANGS:
        raise SystemExit(f"upgrade: --map-lang must be one of {', '.join(MAP_LANGS)}")
    entries = {k: v for k, v in (("root", root), ("lang", lang)) if v is not None}
    if not entries:
        return text
    current = (load_yaml(text) or {}).get("map")
    if current is None:
        return text.rstrip("\n") + "\nmap:\n" + "".join(f"  {k}: {v}\n" for k, v in entries.items())
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(r"^map:\s*(#.*)?$", line)), None)
    if start is None or not isinstance(current, dict):
        raise SystemExit("upgrade: map in repo.yaml is not written as a block (map: on its own line) – edit it by hand")
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    for key, value in entries.items():
        for i in range(start + 1, end):
            if re.match(rf"^\s+{key}:", lines[i]):
                lines[i] = f"  {key}: {value}\n"
                break
        else:
            lines.insert(start + 1, f"  {key}: {value}\n")
            end += 1
    return "".join(lines)


def refresh_framework_files(repo: Path) -> tuple[list[str], list[str]]:
    """Proavus blocks in CLAUDE.md / AGENTS.md and the check workflow from the template."""
    if not TEMPLATE.is_dir():
        raise SystemExit("upgrade: templates/family/ not found – run it from the plugin, not from .proavus")
    changed, warnings = [], []
    for name in BLOCK_FILES:
        block = BLOCK.search((TEMPLATE / name).read_text(encoding="utf-8")).group(0)
        path = repo / name
        if not path.is_file():
            warnings.append(f"{name} is missing – the Proavus block was not added (ask before creating it)")
            continue
        text = path.read_text(encoding="utf-8")
        if not BLOCK.search(text):
            warnings.append(f"{name} has no <!-- proavus:begin/end --> block – not changed")
            continue
        updated = BLOCK.sub(lambda _: block, text, count=1)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(name)
    source, dest = TEMPLATE / WORKFLOW, repo / WORKFLOW
    if not dest.is_file() or dest.read_bytes() != source.read_bytes():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        changed.append(WORKFLOW.as_posix())
    source, dest = TEMPLATE / HOOK, repo / HOOK
    if not dest.is_file() or dest.read_bytes() != source.read_bytes():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        changed.append(HOOK.as_posix())
    return changed, warnings


def upgrade(repo: Path, map_root: str | None = None, map_lang: str | None = None) -> UpgradeResult:
    plan = plan_upgrade(repo)
    if plan.status in ("newer", "migration-missing"):
        raise SystemExit(f"upgrade: {plan.message}")
    yaml_path = repo / "repo.yaml"
    text = set_map(yaml_path.read_text(encoding="utf-8"), map_root, map_lang)  # checks the values first
    install_tools(repo)
    changed = [".proavus/"]
    if plan.migration:
        changed += migrate.migrate(repo, plan.installed, plan.current)
    files, warnings = refresh_framework_files(repo)
    changed += files
    text = set_schema_version(text, plan.current)
    if text != yaml_path.read_text(encoding="utf-8"):
        yaml_path.write_text(text, encoding="utf-8")
        changed.append("repo.yaml")
    if (repo / ".git").exists():
        setup_hooks(repo)
    report = RepoValidator(repo, repo / ".proavus").run()
    return UpgradeResult(plan.installed, plan.current, changed, warnings, report)


def print_plan(plan: UpgradePlan) -> None:
    state = {"upgrade": "upgrade available", "current": "already current", "newer": "cannot upgrade",
             "migration-missing": "cannot upgrade"}[plan.status]
    print(f"Proavus in this repository: {plan.installed or 'not installed'} · plugin: {plan.current} – {state}")
    if plan.message:
        print(plan.message)
    if plan.status in ("newer",):
        return
    print("\nChanges (CHANGELOG):")
    for head, body in plan.changelog or [("none", "")]:
        print(f"## {head}\n{body}\n" if body else f"  {head}")
    print("Schema changes:")
    for line in plan.schema or ["none"]:
        print(f"  {line}")
    print(f"Migration (migrate.py): {'needed' if plan.migration else 'not needed'}")
    if plan.map_missing:
        print(f"Family map: repo.yaml has no map.{' and map.'.join(plan.map_missing)}")
        if plan.candidates:
            print("Possible starting persons (nobody's parent yet):")
            for pid, name in plan.candidates:
                print(f"  {pid}  {name}")
    if plan.marital:
        print("Marital status inside status_as_written – split into marital_status_as_written "
              "(and marital_status) with the user, see method/reading-records.md §4:")
        for rec, key, value in plan.marital:
            print(f"  {rec} {key}: {value!r}")
    if plan.volumes:
        print("Volume inside locator.page – move it into locator.volume with the user "
              "(and list the volumes in source.volumes), see method/reading-records.md §1:")
        for rec, page in plan.volumes:
            print(f"  {rec} page: {page!r}")
    if plan.unexplained:
        print("Confirmed readings without basis – ask the person who confirmed them how the second reading was done "
              "and add basis and checked only from their answer, see method/reading-records.md §5:")
        for rec in plan.unexplained:
            print(f"  {rec}")


# ---------------------------------------------------------- check-private
def check_private(repo: Path) -> int:
    url = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True, text=True)
    if url.returncode != 0:
        print("no remote 'origin' yet – work stays on this computer until the private repository is created")
        return 5
    remote = url.stdout.strip()
    try:
        out = subprocess.run(
            ["gh", "repo", "view", remote, "--json", "nameWithOwner,visibility,isFork,parent"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("cannot tell: GitHub CLI (gh) is not available – run /check")
        return 4
    if out.returncode != 0:
        print("cannot tell: gh could not read the repository (logged in? run /check)")
        return 4
    info = json.loads(out.stdout)
    parent = (info.get("parent") or {}).get("name", "")
    if info.get("isFork") and parent == "proavus":
        print(f"{info['nameWithOwner']} is a FORK of proavus – forks are public; never write family data here")
        return 3
    if info.get("visibility") != "PRIVATE":
        print(f"{info['nameWithOwner']} is {info.get('visibility')} – family data may only be in a PRIVATE repository")
        return 3
    print(f"{info['nameWithOwner']} is private")
    return 0


# ------------------------------------------------------------------ hooks
def setup_hooks(repo: Path) -> list[str]:
    """Switch on .githooks/pre-commit: core.hooksPath (per clone, not saved in git) and the executable bit."""
    check_family_repo(repo, "hooks")
    if not (repo / ".git").exists():
        raise SystemExit(f"hooks: {repo} is not a git repository yet (git init first)")
    hook = repo / HOOK
    if not hook.is_file():
        raise SystemExit(f"hooks: {HOOK.as_posix()} is missing – run /proavus:upgrade (Proavus 0.5.0 or later)")
    done = []
    git = ["git", "-C", str(repo)]
    current = subprocess.run(git + ["config", "--local", "--get", "core.hooksPath"], capture_output=True, text=True).stdout.strip()
    if current != ".githooks":
        subprocess.run(git + ["config", "--local", "core.hooksPath", ".githooks"], check=True)
        done.append("core.hooksPath = .githooks")
    if not hook.stat().st_mode & 0o100:
        hook.chmod(hook.stat().st_mode | 0o755)
        done.append(f"{HOOK.as_posix()} executable")
    staged = subprocess.run(git + ["ls-files", "--stage", "--", HOOK.as_posix()], capture_output=True, text=True).stdout
    if staged and not staged.startswith("100755"):
        # Windows does not keep the executable bit; git must store it for the other members' clones.
        subprocess.run(git + ["update-index", "--chmod=+x", "--", HOOK.as_posix()], check=True)
        done.append(f"{HOOK.as_posix()} executable in git")
    return done


# ----------------------------------------------------------------- access
DIRECT = ("ADMIN", "MAINTAIN")   # may save straight to main
PROPOSE = ("WRITE",)             # saves through a branch and a pull request


def repo_access(info: dict) -> tuple[int, str]:
    """Exit code and a plain sentence from `gh repo view --json` output."""
    name = info.get("nameWithOwner", "?")
    parent = (info.get("parent") or {}).get("name", "")
    if info.get("isFork") and parent == "proavus":
        return 3, f"{name} is a FORK of proavus – forks are public; never write family data here"
    if info.get("visibility") != "PRIVATE":
        return 3, f"{name} is {info.get('visibility')} – family data may only be in a PRIVATE repository"
    permission = info.get("viewerPermission") or "NONE"
    if permission in DIRECT:
        return 0, f"{name} is private; you may save directly ({permission.lower()})"
    if permission in PROPOSE:
        return 2, f"{name} is private; you save through a pull request (write) – a maintainer merges it"
    return 6, f"{name} is private; you may only read ({permission.lower()}) – ask a maintainer for write access"


def access(target: str) -> int:
    """`target` is a family repository folder (its origin) or OWNER/NAME on GitHub."""
    path = Path(target).expanduser()
    if path.is_dir():
        url = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"], capture_output=True, text=True)
        if url.returncode != 0:
            print("no remote 'origin' – not a clone of a GitHub repository")
            return 4
        target = url.stdout.strip()
    try:
        out = subprocess.run(
            ["gh", "repo", "view", target, "--json", "nameWithOwner,visibility,isFork,parent,viewerPermission"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("cannot tell: GitHub CLI (gh) is not available")
        return 4
    if out.returncode != 0:
        if "Could not resolve to a Repository" in out.stderr:
            print(f"{target}: not found, or this GitHub account has no access yet – "
                  "accept the invitation (github.com → notifications) or ask a maintainer to invite you")
            return 7
        print("cannot tell: gh could not read the repository (logged in? gh auth status)")
        return 4
    code, message = repo_access(json.loads(out.stdout))
    print(message)
    return code


# ------------------------------------------------------------- add-member
MEMBER_ROLES = ("researcher", "helper", "maintainer")


def add_member(repo: Path, abbr: str, name: str, role: str = "researcher") -> bool:
    """Append a member to repo.yaml; False if exactly this member is already listed."""
    check_family_repo(repo, "add-member")
    name = name.strip()
    if not re.fullmatch(r"[a-z]{2,4}", abbr):
        raise SystemExit(f"add-member: the abbreviation must be 2–4 lowercase letters a–z, got {abbr!r}")
    if not name:
        raise SystemExit("add-member: the name is empty")
    if role not in MEMBER_ROLES:
        raise SystemExit(f"add-member: role must be one of {', '.join(MEMBER_ROLES)}, got {role!r}")
    path = repo / "repo.yaml"
    text = path.read_text(encoding="utf-8")
    members = (load_yaml(text) or {}).get("members") or []
    for m in members:
        if not isinstance(m, dict):
            continue
        if m.get("abbr") == abbr:
            if str(m.get("name", "")).strip() == name:
                return False
            raise SystemExit(f"add-member: {abbr!r} already belongs to {m.get('name')!r} – choose another abbreviation")
        if str(m.get("name", "")).strip().casefold() == name.casefold():
            raise SystemExit(f"add-member: {name!r} is already listed as {m.get('abbr')!r} – nothing to add")
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(r"^members:\s*(#.*)?$", line)), None)
    if start is None:
        raise SystemExit("add-member: members in repo.yaml is not written as a block (members: on its own line) – edit it by hand")
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    if end > start + 1 and not lines[end - 1].endswith("\n"):
        lines[end - 1] += "\n"
    lines.insert(end, f"  - abbr: {abbr}\n    name: {yaml_str(name)}\n    role: {role}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Family repository helper (Proavus).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("repo")
    p.add_argument("--title", required=True)
    p.add_argument("--member", action="append", default=[], help='abbr:"Full name" (repeatable)')
    p.add_argument("--region", action="append", default=[], help="region code, e.g. cz (repeatable)")
    for name in ("install-tools", "start-here", "check-private", "upgrade-plan", "hooks"):
        sub.add_parser(name).add_argument("repo", nargs="?", default=".")
    p = sub.add_parser("protect-plugin")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--also", action="append", default=[], help="another framework folder to protect (repeatable)")
    p = sub.add_parser("access")
    p.add_argument("target", nargs="?", default=".", help="family repository folder or OWNER/NAME")
    p = sub.add_parser("add-member")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--abbr", required=True, help="2–4 lowercase letters, used in IDs")
    p.add_argument("--name", required=True)
    p.add_argument("--role", choices=MEMBER_ROLES, default="researcher")
    p = sub.add_parser("upgrade")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--map-root", help="starting person of the family map (P-…)")
    p.add_argument("--map-lang", choices=MAP_LANGS, help="language of the map labels")
    args = parser.parse_args(argv)
    if args.cmd == "access":
        return access(args.target)
    repo = Path(args.repo).resolve()

    if args.cmd == "init":
        init(repo, args.title, args.member, args.region)
        print(f"family repository created in {repo} (Proavus {framework_version()})")
        return 0
    if args.cmd == "install-tools":
        install_tools(repo)
        print(f".proavus/ installed (Proavus {framework_version()})")
        return 0
    if args.cmd == "protect-plugin":
        added = protect_plugin(repo, [Path(a).expanduser() for a in args.also])
        print(f".claude/settings.local.json: {len(added)} new deny rules" + "".join(f"\n  {r}" for r in added))
        return 0
    if args.cmd == "hooks":
        done = setup_hooks(repo)
        print("pre-commit hook: " + ("; ".join(done) if done else "already on") + " – every commit is validated")
        return 0
    if args.cmd == "add-member":
        if add_member(repo, args.abbr, args.name, args.role):
            print(f"repo.yaml: added {args.abbr} – {args.name.strip()} ({args.role})")
            return 0
        print(f"repo.yaml: {args.abbr} – {args.name.strip()} is already listed, nothing changed")
        return 1
    if args.cmd == "upgrade-plan":
        plan = plan_upgrade(repo)
        print_plan(plan)
        return {"upgrade": 0, "current": 1}.get(plan.status, 3)
    if args.cmd == "upgrade":
        result = upgrade(repo, args.map_root, args.map_lang)
        report = result.report
        print(f"upgraded Proavus {result.old or 'none'} → {result.new}; changed: {', '.join(result.changed)}")
        for w in result.warnings:
            print(f"WARN  {w}")
        for msg in report.errors:
            print(f"ERROR {msg}")
        print(f"validate: {report.files} files, {len(report.errors)} errors, {len(report.warnings)} warnings")
        print(f"COMMIT: {result.commit_message}")
        return 0 if report.ok else 1
    if args.cmd == "start-here":
        summary, code = start_here(repo)
        print(summary)
        return code
    return check_private(repo)


if __name__ == "__main__":
    sys.exit(main())
