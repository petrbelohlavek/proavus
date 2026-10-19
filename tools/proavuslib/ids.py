"""Entity IDs: <PREFIX>-<YYYYMMDD>-<member>-<3 random chars> (ADR 0024)."""

from __future__ import annotations

import datetime as _dt
import re
import secrets

# entity type -> (ID prefix, directory in the family repository)
ENTITIES: dict[str, tuple[str, str]] = {
    "question": ("Q", "questions"),
    "session": ("S", "sessions"),
    "coverage": ("C", "coverage"),
    "record": ("R", "records"),
    "source": ("SO", "sources"),
    "person": ("P", "people"),
    "relationship": ("RL", "relationships"),
    "assertion": ("A", "assertions"),
    "conflict": ("X", "conflicts"),
    "place": ("PL", "places"),
    "oral": ("O", "oral"),
    "decision": ("D", "decisions"),
    "chronicle": ("CH", "chronicle"),
}
TYPE_BY_PREFIX = {prefix: t for t, (prefix, _) in ENTITIES.items()}
TYPE_BY_DIR = {d: t for t, (_, d) in ENTITIES.items()}

ID_RE = re.compile(
    r"^(?P<prefix>" + "|".join(sorted(TYPE_BY_PREFIX, key=len, reverse=True)) + r")"
    r"-(?P<date>[0-9]{8})-(?P<member>[a-z]{2,4})-(?P<rand>[a-z0-9]{3})$"
)

# No 0/o, 1/l/i: easy to read aloud and to copy by hand.
ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


def parse(id_: str) -> re.Match | None:
    return ID_RE.match(id_) if isinstance(id_, str) else None


def date_ok(id_: str) -> bool:
    m = parse(id_)
    if not m:
        return False
    try:
        _dt.datetime.strptime(m["date"], "%Y%m%d")
    except ValueError:
        return False
    return True


def new_id(entity_type: str, member: str, existing: set[str] = frozenset(),
           today: _dt.date | None = None) -> str:
    prefix = ENTITIES[entity_type][0]
    if not re.fullmatch(r"[a-z]{2,4}", member):
        raise ValueError(f"member abbreviation must be 2–4 lowercase letters: {member!r}")
    day = (today or _dt.date.today()).strftime("%Y%m%d")
    for _ in range(1000):
        candidate = f"{prefix}-{day}-{member}-" + "".join(secrets.choice(ALPHABET) for _ in range(3))
        if candidate not in existing:
            return candidate
    raise RuntimeError("could not find a free ID")
