#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Access to a source and the legal time limit of register entries (ADR 0064).

Usage:  uv run tools/access.py limit REPO --event death --year 1995
        uv run tools/access.py source REPO SO-ID

limit: from which year anyone may see an entry of that kind made in that
year, by the time limits of the repository's regions (regions/<r>/access.yaml;
cz: zákon č. 301/2000 Sb. – birth 100, marriage 75, death 30 years from
the entry). A calculation, not a decision: the archive or office decides.

source: how the source can be read – its own access, else the mode of its
portal from the catalogue (automated, link, manual …) and why.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import access  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402


def main(argv: list[str] | None = None, today: dt.date | None = None) -> int:
    parser = argparse.ArgumentParser(description="Access to a source and legal time limits of register entries (Proavus).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("limit")
    p.add_argument("repo")
    p.add_argument("--event", required=True, help="event type: birth, baptism, marriage, death, burial …")
    p.add_argument("--year", type=int, required=True, help="year of the entry")
    p = sub.add_parser("source")
    p.add_argument("repo")
    p.add_argument("source", help="source ID (SO-…)")
    args = parser.parse_args(argv)
    today = today or dt.date.today()

    v = RepoValidator(Path(args.repo).resolve(), TOOLS_DIR.parent, today=today)
    v.run()
    if args.cmd == "limit":
        lim = access.limit(v.access_rules(), args.event)
        if lim is None:
            print(f"no legal time limit for {args.event} entries in the regions of this repository")
            return 1
        opens = lim.opens(args.year)
        state = "open to anyone now" if opens <= today.year else f"not open to anyone until {opens}"
        print(f"{args.event} entry of {args.year}: {state} – {lim.years} years from the entry for {lim.kind} entries "
              f"({lim.law}, region {lim.region}); the archive or office decides")
        return 0

    src = v.entities.get(args.source)
    if src is None or src.type != "source":
        print(f"access: {args.source} is not a source in this repository", file=sys.stderr)
        return 2
    own = src.data.get("access") if isinstance(src.data.get("access"), dict) else {}
    portal = access.portals(TOOLS_DIR.parent).get(src.data.get("portal") or "")
    if own.get("mode"):
        held = f", held by {own['held_by']}" if own.get("held_by") else ""
        print(f"{src.id}: {own['mode']}{held}" + (f" – {own['note']}" if own.get("note") else ""))
    if portal:
        print(f"portal {portal['id']} ({portal.get('name', '')}): {portal.get('access')} – {portal.get('why', '')}")
    if not own.get("mode") and not portal:
        print(f"{src.id}: no access mode – name its portal (portal: <id>, see archive_fetch.py portals) or write access: {{mode: …}}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
