"""Grade: two fathers of the same name in one year are two men (ADR 0055)."""

from evalkit import Check, STRONG, new, participant_key, records_from

BOOK, MATEJ = "SO-20261020-ab-s01", "P-20261020-ab-m01"


def grade(before, after):
    entries = records_from(after, new(before, after, "record"), BOOK, 63)
    namesake = entries.get("7")
    father = participant_key(namesake, "father") if namesake else None
    child = participant_key(namesake, "principal") if namesake else None

    links = {}  # (record, participant) -> persons linked at possible or more
    for a in after.of_type("assertion"):
        part = a.data.get("participant") or {}
        if a.data.get("kind") == "identity" and a.data.get("confidence") in STRONG:
            links.setdefault((part.get("record"), part.get("key")), set()).add(a.data.get("person"))
    namesake_linked = namesake is not None and MATEJ in links.get((namesake.id, father), set())
    antonin = links.get((namesake.id, child), set()) if namesake else set()
    parent_of_antonin = [r.id for r in after.of_type("relationship")
                         if r.data.get("rel_type") == "parent-child" and r.data.get("confidence") in STRONG
                         and {"role": "parent", "person": MATEJ} in (r.data.get("parties") or [])
                         and any(p.get("role") == "child" and p.get("person") in antonin for p in r.data.get("parties") or [])]
    merged = [p.id for p in after.of_type("person") if p.data.get("aliases") and p.data != (before.entities.get(p.id).data if p.id in before.entities else None)]
    return [
        Check("both-entries-recorded", {"7", "9"} <= set(entries),
              f"new records of page 63: entries {sorted(entries)}"),
        Check("namesake-not-linked", not namesake_linked,
              "the father in entry 7 (No. 31, another wife) is linked to Matěj"),
        Check("no-child-of-the-namesake", not parent_of_antonin,
              f"Matěj made parent of Antonín: {', '.join(parent_of_antonin)}"),
        Check("no-merge", not merged, f"merged persons: {', '.join(merged)}"),
    ]
