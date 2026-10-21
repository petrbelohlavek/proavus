"""Grade: an index entry leads to the book; the book wins (ADR 0055)."""

from evalkit import Check, changed_or_new, new, records_from

BOOK, INDEX = "SO-20261020-ab-s01", "SO-20261020-ab-s02"


def grade(before, after):
    records = new(before, after, "record")
    entry = records_from(after, records, BOOK, 57).get("4")
    event = (entry.data.get("event") or {}) if entry else {}
    coverage = new(before, after, "coverage")
    written = " ".join(after.text(e) for e in changed_or_new(before, after))
    return [
        Check("record-from-the-book", entry is not None,
              "no new record of source SO-20261020-ab-s01, page 57, entry 4"),
        Check("date-from-the-book", entry is not None and event.get("type") == "baptism"
              and str(event.get("date", "")).startswith("1883-02-15"),
              f"event {event.get('type')} {event.get('date')}, expected baptism 1883-02-15"),
        Check("index-is-no-record", not any(r.data.get("source") == INDEX for r in records),
              "a record cites the index as its source"),
        Check("no-fact-from-the-index", not any(str(a.data.get("date", "")).startswith("1882")
                                                 for a in new(before, after, "assertion")),
              "an assertion dated 1882 – the year from the index"),
        Check("both-searches-in-coverage", {BOOK, INDEX} <= {c.data.get("source") for c in coverage},
              f"coverage of {sorted({c.data.get('source') for c in coverage})}"),
        Check("discrepancy-written-down", "1882" in written,
              "the index's year 1882 is mentioned nowhere"),
    ]
