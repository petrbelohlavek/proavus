#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Merge duplicate fact assertions into one (ADR 0063).

Usage:  uv run tools/merge_assertions.py plan REPO [A-ID A-ID …]
        uv run tools/merge_assertions.py apply REPO A-ID A-ID … [--keep A-ID] [--confidence VALUE]

plan shows what a merge would do and changes nothing; without IDs it plans
every group the validator reports ("join their citations into one
assertion"). apply writes it – only after the researcher's yes to the plan:
the kept assertion gets all citations, links to the others are rewritten,
the others are deleted (git keeps them), and the repository is validated.
A plan with problems (another confidence, another evaluation of the same
citation, different places …) writes nothing: the researcher decides first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import merge  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402


def show(p: merge.Plan, ids: list[str]) -> None:
    print(f"Merge {', '.join(ids)}")
    if p.keep:
        print(f"  keep {p.keep}, remove {', '.join(p.drop)}")
        cites = p.data.get("citations") or []
        print(f"  citations after the merge: {len(cites)}")
        for c in cites:
            print("    - " + ", ".join(f"{k}: {v}" for k, v in c.items()))
        if p.data.get("confidence"):
            print(f"  confidence: {p.data['confidence']}")
    for path, found in p.links.items():
        print(f"  link in {path}: {', '.join(found)} → {p.keep}")
    for msg in p.notes:
        print(f"  NOTE {msg}")
    for msg in p.problems:
        print(f"  STOP {msg}")
    print("  ready – apply after the researcher's yes" if p.ok else "  not ready – nothing can be written until the researcher decides")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge duplicate fact assertions into one (Proavus).")
    parser.add_argument("cmd", choices=("plan", "apply"))
    parser.add_argument("repo", help="family repository, e.g. .")
    parser.add_argument("ids", nargs="*", help="the assertions to merge (A-…)")
    parser.add_argument("--keep", help="the assertion to keep (default: the one most linked to, else the oldest ID)")
    parser.add_argument("--confidence", help="the confidence after the merge, when they differ – the researcher's choice")
    args = parser.parse_args(argv)
    repo, framework = Path(args.repo).resolve(), TOOLS_DIR.parent

    if args.cmd == "plan" and not args.ids:
        v = RepoValidator(repo, framework)
        v.run()
        groups = [[a.id for a in g] for g in v.duplicate_fact_groups() if len(g) > 1]
        if not groups:
            print("no duplicate fact assertions")
            return 0
        ok = True
        for ids in groups:
            p = merge.plan(repo, framework, ids)
            show(p, ids)
            ok = ok and p.ok
        return 0 if ok else 1

    if len(args.ids) < 2:
        parser.error("give at least two assertions")
    p = merge.plan(repo, framework, args.ids, keep=args.keep, confidence=args.confidence)
    show(p, args.ids)
    if args.cmd == "plan":
        return 0 if p.ok else 1
    if not p.ok:
        print("apply: nothing written")
        return 1
    for path in merge.apply(repo, framework, p):
        print(f"  written {path}")
    report = RepoValidator(repo, framework).run()
    print(f"validate: {len(report.errors)} errors, {len(report.warnings)} warnings")
    for msg in report.errors:
        print(f"ERROR {msg}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
