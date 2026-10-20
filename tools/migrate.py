#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Migrate the data of a family repository between major schema versions.

Usage:  uv run tools/migrate.py REPO_DIR --from X.Y.Z --to X.Y.Z

Only a breaking schema change raises the major version, and only then is a
migration needed (ADR 0018). Each step from major N to N+1 is one function
in MIGRATIONS that changes the files in place and returns the paths it
changed. There are none yet: schema v0 has had no breaking change.

Exit codes: 0 done or nothing to do, 3 a needed migration is missing.
Run by `family_repo.py upgrade` (/proavus:upgrade), always from the plugin –
the new framework brings the migration.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import versions  # noqa: E402

# from major N → function(repo) migrating to N+1, returns changed paths
MIGRATIONS: dict[int, Callable[[Path], list[str]]] = {}


class MigrationMissing(Exception):
    pass


def needed(old: str, new: str) -> bool:
    return versions.major(new) > versions.major(old)


def steps(old: str, new: str) -> list[int]:
    """Majors to migrate from, in order; raises MigrationMissing if one is not written."""
    todo = list(range(versions.major(old), versions.major(new)))
    missing = [m for m in todo if m not in MIGRATIONS]
    if missing:
        raise MigrationMissing(
            f"migration from schema {old} to {new} needs steps {', '.join(f'{m}→{m + 1}' for m in missing)}, "
            "which this version of Proavus does not have")
    return todo


def migrate(repo: Path, old: str, new: str) -> list[str]:
    changed: list[str] = []
    for m in steps(old, new):
        changed += MIGRATIONS[m](repo)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a Proavus family repository between major versions.")
    parser.add_argument("repo")
    parser.add_argument("--from", dest="old", required=True)
    parser.add_argument("--to", dest="new", required=True)
    args = parser.parse_args(argv)
    if not needed(args.old, args.new):
        print(f"migrate: {args.old} → {args.new} keeps the major version – nothing to migrate")
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
