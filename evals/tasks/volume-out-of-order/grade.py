"""Grade: a late entry stands in another volume of the source (ADR 0055, 0058)."""

from evalkit import Check, new

BOOK = "SO-20261024-ab-s03"


def _vol(value) -> str:
    return str(value).strip().casefold() if value is not None else ""


def grade(before, after):
    records = [r for r in new(before, after, "record") if r.data.get("source") == BOOK]
    entry = next((r for r in records if (r.data.get("event") or {}).get("type") == "marriage"
                  and "14" in str((r.data.get("locator") or {}).get("page", ""))), None)
    loc = (entry.data.get("locator") or {}) if entry else {}
    ranges = [r for c in new(before, after, "coverage") if c.data.get("source") == BOOK
              for r in c.data.get("ranges") or [] if isinstance(r, dict)]
    volumes = {_vol(r.get("volume")) for r in ranges}
    return [
        Check("record-from-volume-II", entry is not None and _vol(loc.get("volume")) == "ii",
              f"marriage record of {BOOK}, page 14: volume {loc.get('volume')!r}" if entry else "no marriage record of page 14"),
        Check("volume-in-its-own-field", entry is not None and str(loc.get("page")).strip() == "14",
              f"locator.page {loc.get('page')!r}, expected 14 with the volume in locator.volume"),
        Check("date-from-the-entry", entry is not None and str((entry.data.get("event") or {}).get("date", "")).startswith("1877-11-20"),
              f"event date {(entry.data.get('event') or {}).get('date') if entry else None}, expected 1877-11-20"),
        Check("both-volumes-in-coverage", {"i", "ii"} <= volumes,
              f"coverage ranges of {BOOK} name volumes {sorted(v for v in volumes if v)}"),
    ]
