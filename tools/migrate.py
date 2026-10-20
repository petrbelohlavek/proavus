#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Migrate the data of a family repository to a newer Proavus version.

Usage:  uv run tools/migrate.py REPO_DIR --from X.Y.Z --to X.Y.Z

Each migration belongs to the version that brought it (MIGRATIONS, keyed by
that version) and runs when an upgrade crosses it (ADR 0030):

- a **major** version (breaking schema change, ADR 0018) must have one –
  without it the upgrade is refused;
- a **minor** version may have one that rewrites data into the new preferred
  form while the old form stays valid (e.g. 0.3.0: crop → crops).

A migration changes files in place, is safe to run twice and returns the
paths it changed. Exit codes: 0 done or nothing to do, 3 a needed migration
is missing. Run by `family_repo.py upgrade` (/proavus:upgrade), always from
the plugin – the new framework brings the migration.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import versions  # noqa: E402
from proavuslib.frontmatter import join, split  # noqa: E402


class MigrationMissing(Exception):
    pass


def _rewrite(repo: Path, folder: str, change: Callable[[dict], bool]) -> list[str]:
    """Apply change(header) to every entity file in a folder; rewrite the ones it changed."""
    changed = []
    base = repo / folder
    for path in sorted(base.rglob("*.md")) if base.is_dir() else []:
        if path.name.lower() == "readme.md" or path.name.startswith("_"):
            continue
        try:
            data, body = split(path.read_text(encoding="utf-8"))
        except ValueError:
            continue  # broken files are the validator's business
        if change(data):
            path.write_text(join(data, body), encoding="utf-8")
            changed.append(path.relative_to(repo).as_posix())
    return changed


def to_0_3_0(repo: Path) -> list[str]:
    """Schema 0.3: one crop → crops (ADR 0031); human tasks as text → open tasks (ADR 0037)."""

    def crops(data: dict) -> bool:
        crop = data.get("crop")
        if not isinstance(crop, str) or "crops" in data:
            return False
        items = list(data.items())
        data.clear()
        for key, value in items:
            if key == "crop":
                data["crops"] = [{"path": crop}]
            else:
                data[key] = value
        return True

    def tasks(data: dict) -> bool:
        current = data.get("human_tasks")
        if not isinstance(current, list) or not any(isinstance(t, str) for t in current):
            return False
        data["human_tasks"] = [{"task": t, "status": "open"} if isinstance(t, str) else t for t in current]
        return True

    return _rewrite(repo, "records", crops) + _rewrite(repo, "sessions", tasks)


MIGRATIONS: dict[str, Callable[[Path], list[str]]] = {
    "0.3.0": to_0_3_0,
}


def steps(old: str, new: str) -> list[str]:
    """Versions whose migration runs from old to new, in order; raises MigrationMissing
    when a crossed major version has none."""
    lo, hi = versions.parse(old), versions.parse(new)
    todo = sorted((v for v in MIGRATIONS if lo < versions.parse(v) <= hi), key=versions.parse)
    missing = [f"{m}.0.0" for m in range(lo[0] + 1, hi[0] + 1) if f"{m}.0.0" not in MIGRATIONS]
    if missing:
        raise MigrationMissing(
            f"upgrade from {old} to {new} crosses major version {', '.join(missing)} without a migration, "
            "which this version of Proavus does not have")
    return todo


def needed(old: str, new: str) -> bool:
    """Does an upgrade from old to new run (or need) any migration?"""
    lo, hi = versions.parse(old), versions.parse(new)
    return hi[0] > lo[0] or any(lo < versions.parse(v) <= hi for v in MIGRATIONS)


def migrate(repo: Path, old: str, new: str) -> list[str]:
    changed: list[str] = []
    for version in steps(old, new):
        changed += MIGRATIONS[version](repo)
    return list(dict.fromkeys(changed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a Proavus family repository to a newer version.")
    parser.add_argument("repo")
    parser.add_argument("--from", dest="old", required=True)
    parser.add_argument("--to", dest="new", required=True)
    args = parser.parse_args(argv)
    if not needed(args.old, args.new):
        print(f"migrate: {args.old} → {args.new} – nothing to migrate")
        return 0
    try:
        changed = migrate(Path(args.repo).resolve(), args.old, args.new)
    except MigrationMissing as exc:
        print(f"migrate: {exc}")
        return 3
    print(f"migrate: {args.old} → {args.new}, {len(changed)} files changed" + "".join(f"\n  {c}" for c in changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
