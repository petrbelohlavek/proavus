#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print new collision-free entity IDs.

Usage:  uv run tools/new_id.py TYPE MEMBER [--repo DIR] [--count N]
        e.g. uv run tools/new_id.py question jn  →  Q-20261020-jn-k7m
        --count 20 prints 20 different IDs, one per line (one start of uv for many files)

The ID is checked against all file names in the family repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from proavuslib import ids  # noqa: E402

MAX_COUNT = 200


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
    parser.add_argument("--count", type=int, default=1, help=f"how many IDs (1–{MAX_COUNT}, default 1)")
    args = parser.parse_args(argv)
    if not 1 <= args.count <= MAX_COUNT:
        print(f"new_id: --count must be between 1 and {MAX_COUNT}", file=sys.stderr)
        return 2
    try:
        taken = existing_ids(Path(args.repo))
        for _ in range(args.count):
            new = ids.new_id(args.type, args.member, taken)
            taken.add(new)
            print(new)
    except ValueError as exc:
        print(f"new_id: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
