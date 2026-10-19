"""Subset of the Extended Date/Time Format (EDTF, ISO 8601-2) for historical dates.

Supported: 1935 · 1935-04 · 1935-04-12 · qualifiers ? ~ % at the end ·
unspecified digits 19XX, 193X, 1935-XX · intervals 1904/1906, ../1900, 1900/..

parse() returns the widest possible (earliest, latest) years, so checks only
flag what is impossible under every reading of the date.
"""

from __future__ import annotations

import calendar
import re

_SINGLE = re.compile(
    r"^(?P<year>[0-9]{4}|[0-9]{3}X|[0-9]{2}XX)"
    r"(?:-(?P<month>[0-9]{2}|XX)(?:-(?P<day>[0-9]{2}|XX))?)?"
    r"(?P<qual>[?~%])?$"
)

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
        if month and month != "XX":
            mi = int(month)
            if not 1 <= mi <= 12:
                raise ValueError(f"invalid month in {text!r}")
            if day and day != "XX":
                if not 1 <= int(day) <= calendar.monthrange(lo, mi)[1]:
                    raise ValueError(f"invalid day in {text!r}")
        elif day and day != "XX":
            raise ValueError(f"day with unspecified month: {text!r}")
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
