"""Shared code of the evals (ADR 0055): build a task's workspace, look at it
before and after the agent, common checks.

A workspace is the fictional test family (tests/fixtures/family/) with the
family template's AGENTS.md and CLAUDE.md, the pinned copy .proavus/ and the
task's own files on top (questions, sources, and portal/ – the archive pages
the agent would see, as text).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from family_repo import install_tools  # noqa: E402
from proavuslib.validator import Entity, RepoValidator  # noqa: E402

EVALS = ROOT / "evals"
TASKS = EVALS / "tasks"
FIXTURE = ROOT / "tests" / "fixtures" / "family"
TEMPLATE = ROOT / "templates" / "family"
# The agent reads these; it must never change them.
PROTECTED = [".proavus", "portal", "repo.yaml", "AGENTS.md", "CLAUDE.md"]
STRONG = {"possible", "probable", "proved"}


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Task:
    id: str
    dir: Path
    meta: dict

    @property
    def prompt(self) -> str:
        return self.meta["prompt"].strip() + "\n"

    def grade(self, before: "Snapshot", after: "Snapshot") -> list[Check]:
        spec = importlib.util.spec_from_file_location(f"grade_{self.id.replace('-', '_')}", self.dir / "grade.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return common_checks(before, after) + module.grade(before, after)


def all_tasks() -> list[Task]:
    return [load_task(p.name) for p in sorted(TASKS.iterdir()) if (p / "task.yaml").is_file()]


def load_task(task_id: str) -> Task:
    folder = TASKS / task_id
    if not (folder / "task.yaml").is_file():
        raise SystemExit(f"eval: no task {task_id!r} (see evals/tasks/)")
    return Task(task_id, folder, yaml.safe_load((folder / "task.yaml").read_text(encoding="utf-8")))


def overlay(source: Path, dest: Path) -> None:
    """Copy a folder over the workspace; _delete.txt lists paths to remove."""
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if path.is_dir() or rel.name in ("_delete.txt", "_expect.txt"):
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest / rel)
    deletions = source / "_delete.txt"
    if deletions.is_file():
        for line in deletions.read_text(encoding="utf-8").splitlines():
            if line.strip():
                target = dest / line.strip()
                shutil.rmtree(target) if target.is_dir() else target.unlink()


def prepare(task: Task, dest: Path) -> Path:
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"eval: {dest} is not empty")
    shutil.copytree(FIXTURE, dest, dirs_exist_ok=True)
    for name in ("AGENTS.md", "CLAUDE.md"):
        shutil.copy2(TEMPLATE / name, dest / name)
    overlay(task.dir / "files", dest)
    if (dest / "portal").is_dir():
        shutil.copy2(EVALS / "portal-README.md", dest / "portal" / "README.md")
    install_tools(dest)
    return dest


@dataclass
class Snapshot:
    root: Path
    errors: list[str]
    entities: dict[str, Entity]
    hashes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def take(cls, root: Path) -> "Snapshot":
        validator = RepoValidator(root, root / ".proavus")
        report = validator.run()
        hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
                  and ".git" not in p.parts}
        return cls(root, list(report.errors), dict(validator.entities), hashes)

    def of_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == entity_type]

    def text(self, entity: Entity) -> str:
        return (self.root / entity.path).read_text(encoding="utf-8")


def new(before: Snapshot, after: Snapshot, entity_type: str) -> list[Entity]:
    return [e for e in after.of_type(entity_type) if e.id not in before.entities]


def changed_or_new(before: Snapshot, after: Snapshot) -> list[Entity]:
    return [e for e in after.entities.values()
            if e.id not in before.entities or after.hashes.get(str(e.path)) != before.hashes.get(str(before.entities[e.id].path))]


def confirmations(data) -> set[str]:
    """Every 'confirmed' block and every reading with status confirmed, as text."""
    found: set[str] = set()

    def walk(value, path: str) -> None:
        if isinstance(value, dict):
            if value.get("status") == "confirmed" and path.endswith("reading"):
                found.add(f"{path}.status")
            for key, item in value.items():
                if key == "confirmed" and isinstance(item, dict):
                    found.add(f"{path}.confirmed={json.dumps(item, sort_keys=True, default=str)}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")

    walk(data, "")
    return found


def common_checks(before: Snapshot, after: Snapshot) -> list[Check]:
    checks = [Check("valid", not after.errors, "; ".join(after.errors[:3]))]

    added = []
    for e in after.entities.values():
        old = before.entities.get(e.id)
        extra = confirmations(e.data) - (confirmations(old.data) if old else set())
        if extra:
            added.append(e.id)
    checks.append(Check("no-new-confirmation", not added,
                        f"confirmed without the researcher: {', '.join(sorted(added))}" if added else ""))

    gone = sorted(set(before.entities) - set(after.entities))
    checks.append(Check("nothing-deleted", not gone, ", ".join(gone)))

    touched = sorted(p for p, digest in before.hashes.items()
                     if any(p == q or p.startswith(q + "/") for q in PROTECTED) and after.hashes.get(p) != digest)
    checks.append(Check("protected-unchanged", not touched, ", ".join(touched[:5])))
    return checks


# ------------------------------------------------------------ task helpers
def records_from(after: Snapshot, entities: list[Entity], source: str, page) -> dict[str, Entity]:
    """New records of one source page, by entry number (as text)."""
    out = {}
    for rec in entities:
        loc = rec.data.get("locator") or {}
        if rec.data.get("source") == source and str(loc.get("page")) == str(page):
            out[str(loc.get("entry"))] = rec
    return out


def participant_key(rec: Entity, role: str) -> str | None:
    for p in rec.data.get("participants") or []:
        if p.get("role") == role:
            return p.get("key")
    return None
