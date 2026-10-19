#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Validate a Proavus family repository.

Usage:  uv run tools/validate.py [REPO_DIR]      (default: current directory)

Checks headers against the schema (with the regional extensions switched on
in repo.yaml), IDs and file names, links, the identity gate, living persons,
impossible dates and negative searches. Exit code 1 if there are errors.
Warnings (e.g. a value missing from a vocabulary) never block.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib.validator import RepoValidator  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Proavus family repository.")
    parser.add_argument("repo", nargs="?", default=".", help="family repository (default: .)")
    parser.add_argument("-q", "--quiet", action="store_true", help="errors only")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    # The framework root is the parent of tools/ – the framework itself or
    # the pinned copy .proavus/ in a family repository (ADR 0014).
    report = RepoValidator(repo, TOOLS_DIR.parent).run()

    for msg in report.errors:
        print(f"ERROR {msg}")
    if not args.quiet:
        for msg in report.warnings:
            print(f"WARN  {msg}")
        for msg in report.notes:
            print(f"NOTE  {msg}")
    print(
        f"validate: {report.files} files, {len(report.errors)} errors, "
        f"{len(report.warnings)} warnings, {len(report.notes)} schema gaps"
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
