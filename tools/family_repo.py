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
  family_repo.py check-private DIR
      check that the repository's origin is private and not a fork of proavus
      exit 0 = private · 3 = public or a fork (do not write) · 4 = cannot tell
      · 5 = no remote yet

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
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FRAMEWORK = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib.validator import RepoValidator  # noqa: E402

TEMPLATE = FRAMEWORK / "templates" / "family"
# An existing empty repository may contain only these (a clone, plus the
# per-machine settings Claude Code may create when the folder is opened).
EMPTY_REPO_ENTRIES = {".git", ".claude"}
# What goes into .proavus/ (ADR 0014). guard_names.py is framework-only.
COPY_DIRS = ["schema"]
COPY_TOOLS = ["validate.py", "new_id.py", "family_repo.py", "build_views.py"]
COPY_METHOD = ["rules.md", "rules.cs.md", "reading-records.md"]

PROAVUS_README = """# .proavus – pinned copy of the Proavus framework

Managed by `/proavus:upgrade`; do not edit. Version: see `VERSION`.
Lets every member and the GitHub check run the same tools without access to
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
    for ext in sorted((FRAMEWORK / "regions").glob("*/schema-ext.yaml")):
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
def start_here(repo: Path, today: dt.date | None = None) -> tuple[str, int]:
    today = today or dt.date.today()
    v = RepoValidator(repo, FRAMEWORK, today=today)
    report = v.run()
    e = v.entities
    of = v.of_type
    lines = [
        "<!-- GENERATED by /start – do not edit, not saved in git -->",
        f"# START HERE – {today.isoformat()}",
        "",
    ]
    installed = installed_version(repo)
    current = framework_version()
    if installed and installed != current:
        lines += [f"> Proavus in this repository: {installed}, plugin: {current} – run `/proavus:upgrade`.", ""]

    status = "OK" if report.ok else f"{len(report.errors)} ERRORS – fix before saving"
    lines += [f"**Check:** {status} · {report.files} files · {len(report.warnings)} warnings · {len(report.notes)} schema gaps", ""]
    for msg in report.errors[:10]:
        lines.append(f"- ERROR {msg}")
    if len(report.errors) > 10:
        lines.append(f"- … and {len(report.errors) - 10} more (`uv run .proavus/tools/validate.py .`)")
    if report.errors:
        lines.append("")

    open_q = [q for q in of("question") if q.data.get("status") in ("open", "in-progress")]
    lines += ["## Open questions", ""]
    if open_q:
        lines += ["| ID | Question | Status | Who |", "|---|---|---|---|"]
        for q in sorted(open_q, key=lambda q: q.id):
            lines.append(f"| {q.id} | {q.data.get('title', '')} | {q.data.get('status')} | {q.data.get('claimed_by', '–')} |")
    else:
        lines.append("No open questions yet – start by writing one.")
    lines.append("")

    sessions = sorted(of("session"), key=lambda s: (s.data.get("date", ""), s.id), reverse=True)[:5]
    lines += ["## Last sessions and next steps", ""]
    if sessions:
        for s in sessions:
            lines.append(f"- **{s.data.get('date')}** ({s.data.get('by')}) {s.id}: {s.data.get('next_step', '')}")
            for task in s.data.get("human_tasks") or []:
                lines.append(f"  - human task: {task}")
    else:
        lines.append("No sessions yet.")
    lines.append("")

    read_once = [r for r in of("record") if (r.data.get("reading") or {}).get("status") == "read-once"]
    disputed = [r for r in of("record") if (r.data.get("reading") or {}).get("status") == "disputed"]
    conflicts = [c for c in of("conflict") if c.data.get("status") in ("open", "unresolved")]
    lines += ["## Waiting for a human", ""]
    lines.append(f"- records read once (second reading needed before identity): {len(read_once)}"
                 + (" – " + ", ".join(r.id for r in read_once[:10]) if read_once else ""))
    lines.append(f"- disputed readings: {len(disputed)}" + (" – " + ", ".join(r.id for r in disputed) if disputed else ""))
    lines.append(f"- open conflicts: {len(conflicts)}" + (" – " + ", ".join(c.id for c in conflicts) if conflicts else ""))
    lines.append("")

    counts = {t: len(of(t)) for t in ("person", "record", "assertion", "relationship", "coverage", "source")}
    lines += ["## Size", "", " · ".join(f"{n} {t}" for t, n in counts.items()), ""]

    (repo / "START-HERE.md").write_text("\n".join(lines), encoding="utf-8")
    summary = f"START-HERE.md written: {len(open_q)} open questions, {len(read_once)} records read once, check {status}"
    return summary, 0 if report.ok else 1


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Family repository helper (Proavus).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("repo")
    p.add_argument("--title", required=True)
    p.add_argument("--member", action="append", default=[], help='abbr:"Full name" (repeatable)')
    p.add_argument("--region", action="append", default=[], help="region code, e.g. cz (repeatable)")
    for name in ("install-tools", "start-here", "check-private"):
        sub.add_parser(name).add_argument("repo", nargs="?", default=".")
    p = sub.add_parser("protect-plugin")
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--also", action="append", default=[], help="another framework folder to protect (repeatable)")
    args = parser.parse_args(argv)
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
    if args.cmd == "start-here":
        summary, code = start_here(repo)
        print(summary)
        return code
    return check_private(repo)


if __name__ == "__main__":
    sys.exit(main())
