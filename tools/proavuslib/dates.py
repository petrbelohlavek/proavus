"""Dates in words: EDTF subset and ISO dates for people to read (ADR 0029)."""

from __future__ import annotations

import re

from . import edtf

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "cs": ["leden", "únor", "březen", "duben", "květen", "červen", "červenec", "srpen",
           "září", "říjen", "listopad", "prosinec"],
}
DATE_WORDS = {"en": {"about": "about", "before": "before", "after": "after"},
              "cs": {"about": "kolem", "before": "před", "after": "po"}}
_EDTF = re.compile(r"^([0-9]{4}|[0-9]{3}X|[0-9]{2}XX)(?:-([0-9X]{2})(?:-([0-9X]{2}))?)?([?~%])?$")


def _choices(numbers: list[int], fmt) -> str:
    """10–19 for a run, 5/15/25 otherwise."""
    if len(numbers) > 2 and numbers == list(range(numbers[0], numbers[-1] + 1)):
        return f"{fmt(numbers[0])}–{fmt(numbers[-1])}"
    return "/".join(fmt(n) for n in numbers)


def _partial(year: str, month: str, day: str | None, lang: str) -> str | None:
    """Month or day with single unspecified digits (1855-02-1X, 1855-1X), ADR 0045."""
    try:
        expanded = edtf.expand(f"{year}-{month}" + (f"-{day}" if day else ""))
    except ValueError:
        return None
    if expanded is None:
        return None
    _, months, days, _ = expanded
    names = MONTHS.get(lang, MONTHS["en"])
    if days is None:
        return f"{_choices(months, lambda m: names[m - 1])} {year}"
    if len(months) != 1:
        return None                     # unspecified digits in both month and day: keep EDTF
    mo = months[0]
    if lang == "cs":
        return f"{_choices(days, lambda d: f'{d}.')} {mo}. {year}"
    return f"{_choices(days, str)} {names[mo - 1]} {year}"


def human_date(value, lang: str = "en") -> str:
    """EDTF (subset) or ISO date in words: cs 13. 5. 1958, kolem 1868, před 26. 1. 1836, 1946/1947."""
    if value is None:
        return ""
    text = str(value).strip()
    words = DATE_WORDS.get(lang, DATE_WORDS["en"])
    if "/" in text:
        start, _, end = text.partition("/")
        if start in ("", "..") and end not in ("", ".."):
            return f"{words['before']} {human_date(end, lang)}"
        if end in ("", "..") and start not in ("", ".."):
            return f"{words['after']} {human_date(start, lang)}"
        return f"{human_date(start, lang)}/{human_date(end, lang)}"
    m = _EDTF.match(text)
    if not m:
        return text
    year, month, day, qual = m.groups()
    months = MONTHS.get(lang, MONTHS["en"])
    if "X" in year:
        core = f"{year.replace('X', '0')}–{year.replace('X', '9')}"
    elif month and (("X" in month and month != "XX") or (day and "X" in day and day != "XX")):
        core = _partial(year, month, day if day and day != "XX" else None, lang)
        if core is None:
            return text
    elif month and month != "XX" and 1 <= int(month) <= 12:
        if day and day != "XX":
            core = f"{int(day)}. {int(month)}. {year}" if lang == "cs" else f"{int(day)} {months[int(month) - 1]} {year}"
        else:
            core = f"{months[int(month) - 1]} {year}"
    else:
        core = year
    if qual in ("~", "%"):
        core = f"{words['about']} {core}"
    return core + ("?" if qual in ("?", "%") else "")


def short_year(value) -> str:
    """Compact year for the marriage label: ~1877, 1877?, <1836, >1900."""
    text = str(value)
    m = re.search(r"[0-9]{4}|[0-9]{3}X|[0-9]{2}XX", text)
    if not m:
        return ""
    prefix = "<" if text.startswith(("../", "/")) else ">" if text.endswith(("/..", "/")) else "~" if re.search(r"[~%]", text) else ""
    return prefix + m.group(0) + ("?" if re.search(r"[?%]", text) else "")
