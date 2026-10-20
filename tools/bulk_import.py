#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Create many entities from one plan file – for converting older notes (docs/import.md, ADR 0042).

Usage:  uv run .proavus/tools/bulk_import.py PLAN.yaml [--repo .] [--member ab] [--dry-run]

The plan lists entities with symbolic keys (`key: matej`) and links them with
`@key`; every entity gets a new ID. --dry-run shows the files and the
validator's verdict without writing anything. Without it the batch is written
only if it has no validation errors and no file exists yet. The keys and their
IDs are kept in archive/import-keys.yaml (--keys), so a later plan can link
`@matej` from an earlier one. Every entry of the old diary (diary:) must be
linked by an entity (from_diary:).

Exit codes: 0 ok · 1 errors (nothing written) · 2 diary entries without a link.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib.bulk import BulkError, batch_from_plan, load_plan  # noqa: E402
from proavuslib.frontmatter import load_yaml  # noqa: E402

DEFAULT_KEYS = Path("archive") / "import-keys.yaml"


def read_keys(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = load_yaml(path.read_text(encoding="utf-8")) or {}
    keys = data.get("keys") if isinstance(data, dict) else None
    return {str(k): str(v) for k, v in (keys or {}).items()}


def write_keys(path: Path, keys: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Keys of the bulk imports (tools/bulk_import.py) and the IDs they got.",
             "# A later plan may link these keys as @key. Do not edit by hand.", "keys:"]
    lines += [f"  {k}: {v}" for k, v in keys.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create many entities from one plan (Proavus).")
    parser.add_argument("plan", help="plan file (YAML), see docs/import.md")
    parser.add_argument("--repo", default=".", help="family repository (default: .)")
    parser.add_argument("--member", help="member abbreviation for the new IDs (default: member: in the plan)")
    parser.add_argument("--keys", help=f"key map of earlier imports (default: REPO/{DEFAULT_KEYS})")
    parser.add_argument("--dry-run", action="store_true", help="show what would be written, write nothing")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    keys_path = Path(args.keys).resolve() if args.keys else repo / DEFAULT_KEYS
    if not (repo / "repo.yaml").is_file():
        print(f"bulk_import: {repo} has no repo.yaml – not a family repository", file=sys.stderr)
        return 1
    try:
        batch = batch_from_plan(load_plan(Path(args.plan)), repo, TOOLS_DIR.parent, args.member,
                                known_keys=read_keys(keys_path))
        files = batch.files()
        missing = batch.missing_diary()
        report = batch.preview()
    except BulkError as exc:
        print(f"bulk_import: {exc}", file=sys.stderr)
        return 1
    for (rel, _), item in zip(files, batch.items):
        print(f"{'would write' if args.dry_run else 'write'} {rel}  ({item.key})")
    for msg in report.errors:
        print(f"ERROR {msg}")
    for msg in report.warnings:
        print(f"WARN  {msg}")
    for ref in missing:
        print(f"DIARY {ref}: no entity links this entry of the old diary (from_diary)")
    print(f"{len(files)} entities, {len(report.errors)} validation errors, {len(report.warnings)} warnings, "
          f"{len(missing)} of {len(batch.diary)} diary entries without a link")
    if report.errors:
        print("nothing written – fix the plan")
        return 1
    if args.dry_run:
        return 2 if missing else 0
    if missing:
        print("nothing written – link every diary entry (from_diary), or drop it from the diary list with a reason")
        return 2
    try:
        batch.write()
    except BulkError as exc:
        print(f"bulk_import: {exc}", file=sys.stderr)
        return 1
    write_keys(keys_path, batch.key_map())
    print(f"written; keys in {keys_path.relative_to(repo) if keys_path.is_relative_to(repo) else keys_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
