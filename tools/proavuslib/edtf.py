"""Subset of the Extended Date/Time Format (EDTF, ISO 8601-2) for historical dates.

Supported: 1935 · 1935-04 · 1935-04-12 · qualifiers ? ~ % at the end ·
unspecified digits 19XX, 193X, 1935-XX · intervals 1904/1906, ../1900, 1900/..
· single unspecified digits in month and day, e.g. 1855-02-1X (10th–19th),
1855-1X (October–December), 1855-02-X5 (5th, 15th or 25th) – EDTF level 2
"unspecified digit", limited to month and day of a known year (ADR 0045).

parse() returns the widest possible (earliest, latest) years, so checks only
flag what is impossible under every reading of the date.
"""

from __future__ import annotations

import calendar
import re

_SINGLE = re.compile(
    r"^(?P<year>[0-9]{4}|[0-9]{3}X|[0-9]{2}XX)"
    r"(?:-(?P<month>[0-9X]{2})(?:-(?P<day>[0-9X]{2}))?)?"
    r"(?P<qual>[?~%])?$"
)


def _fits(pattern: str, n: int) -> bool:
    """Does the two-digit number n fit a pattern like 1X, X5, XX, 07?"""
    return all(p in ("X", d) for p, d in zip(pattern, f"{n:02d}"))


def expand(text: str) -> tuple[int, list[int] | None, list[int] | None, str | None] | None:
    """A single date of a known year: (year, possible months, possible days, qualifier).

    None for a year with unspecified digits or an interval. Months or days are
    None when not given. Raises ValueError when no real date fits.
    """
    m = _SINGLE.match(str(text).strip())
    if not m:
        raise ValueError(f"not an EDTF date: {text!r}")
    year, month, day, qual = m["year"], m["month"], m["day"], m["qual"]
    if "X" in year:
        return None
    y = int(year)
    months = None if month is None else [mo for mo in range(1, 13) if _fits(month, mo)]
    if months == []:
        raise ValueError(f"invalid month in {text!r}")
    days = None
    if day is not None:
        days = sorted({d for mo in months for d in range(1, calendar.monthrange(y, mo)[1] + 1) if _fits(day, d)})
        if not days:
            raise ValueError(f"invalid day in {text!r}")
    return y, months, days, qual

# Approximate or uncertain dates are widened by this many years for checks.
FUZZ = 2
OPEN_LO, OPEN_HI = 0, 9999


def _single(text: str) -> tuple[int, int]:
    m = _SINGLE.match(text)
    if not m:
        raise ValueError(f"not an EDTF date: {text!r}")
    year, month, day, qual = m["year"], m["month"], m["day"], m["qual"]
    if "X" in year:
        if month or day:
            raise ValueError(f"month/day with unspecified year: {text!r}")
        lo, hi = int(year.replace("X", "0")), int(year.replace("X", "9"))
    else:
        lo = hi = int(year)
        if month == "XX" and day and day != "XX":
            raise ValueError(f"day with unspecified month: {text!r}")
        expand(text)   # some real month and day must fit (1855-02-3X does not)
    if qual:
        lo, hi = lo - FUZZ, hi + FUZZ
    return lo, hi


def parse(value: str | int) -> tuple[int, int]:
    text = str(value).strip()
    if "/" in text:
        start, _, end = text.partition("/")
        lo = OPEN_LO if start in ("", "..") else _single(start)[0]
        hi = OPEN_HI if end in ("", "..") else _single(end)[1]
        if start in ("", "..") and end in ("", ".."):
            raise ValueError(f"interval open on both ends: {text!r}")
        if lo > hi:
            raise ValueError(f"interval ends before it starts: {text!r}")
        return lo, hi
    return _single(text)


def is_valid(value: object) -> bool:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return False
    try:
        parse(value)
    except ValueError:
        return False
    return True
