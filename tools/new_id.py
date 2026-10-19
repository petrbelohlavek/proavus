#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print a new collision-free entity ID.

Usage:  uv run tools/new_id.py TYPE MEMBER [--repo DIR]
        e.g. uv run tools/new_id.py question jn  →  Q-20261020-jn-k7m

The ID is checked against all file names in the family repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from proavuslib import ids  # noqa: E402


def existing_ids(repo: Path) -> set[str]:
    found = set()
    for _, dirname in ids.ENTITIES.values():
        base = repo / dirname
        if base.is_dir():
            for path in base.rglob("*.md"):
                found.add(path.stem.split("--", 1)[0])
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a new entity ID.")
    parser.add_argument("type", choices=sorted(ids.ENTITIES))
    parser.add_argument("member", help="member abbreviation from repo.yaml")
    parser.add_argument("--repo", default=".", help="family repository (default: .)")
    args = parser.parse_args(argv)
    try:
        print(ids.new_id(args.type, args.member, existing_ids(Path(args.repo))))
    except ValueError as exc:
        print(f"new_id: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
