"""Access to sources: the portal catalogue and legal time limits (ADR 0041, 0050, 0064).

Portals come from regions/*/portals.yaml, time limits from
regions/<region>/access.yaml – both inside the framework or its pinned copy
.proavus/. A time limit is a calculation, not a decision: it says from
which year anyone may see an entry; the archive or office decides.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import load_yaml

MODES = ("automated", "link", "manual", "on-site", "request", "none")
# How much a mode allows, for comparing a source with its portal.
REACH = {"automated": 3, "link": 2, "manual": 1, "on-site": 1, "request": 1, "none": 0}


def portals(framework_root: Path) -> dict[str, dict]:
    """Portal entries by id from every regional package."""
    out: dict[str, dict] = {}
    for path in sorted((framework_root / "regions").glob("*/portals.yaml")):
        for entry in (load_yaml(path.read_text(encoding="utf-8")) or {}).get("portals") or []:
            if isinstance(entry, dict) and entry.get("id"):
                out.setdefault(entry["id"], entry)
    return out


@dataclass
class Limit:
    region: str
    law: str
    kind: str          # birth · marriage · partnership · death
    years: int

    def opens(self, entry_year: int) -> int:
        """First year in which anyone may see an entry made in entry_year."""
        return entry_year + self.years


def rules(framework_root: Path, regions: list[str]) -> dict[str, dict]:
    """access.yaml of the repository's regions, by region."""
    out = {}
    for region in regions or []:
        path = framework_root / "regions" / str(region) / "access.yaml"
        if path.is_file():
            out[str(region)] = load_yaml(path.read_text(encoding="utf-8")) or {}
    return out


def limit(all_rules: dict[str, dict], event_type: str) -> Limit | None:
    """The time limit for entries of this event type (the first region that has one)."""
    for region, r in all_rules.items():
        kind = (r.get("events") or {}).get(event_type, event_type)
        years = (r.get("entry_access") or {}).get(kind)
        if isinstance(years, int):
            return Limit(region, str(r.get("law", "")), kind, years)
    return None


def last_year(dates) -> int | None:
    """The latest year an EDTF date or range may mean: 1935 → 1935, 1930/1960 → 1960, 193X → 1939, ../1900 → 1900."""
    text = str(dates).strip()
    if not text:
        return None
    end = text.split("/")[-1]
    if end in ("..", ""):
        return None
    m = re.match(r"^(\d{2})(\d|X)(\d|X)", end)
    if not m:
        return None
    return int(m.group(1) + (m.group(2) if m.group(2) != "X" else "9") + (m.group(3) if m.group(3) != "X" else "9"))
