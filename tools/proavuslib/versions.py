"""Semantic versions of Proavus (one version for the whole repository, ADR 0018)."""

from __future__ import annotations

import re

_VERSION = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")


def parse(text: str) -> tuple[int, int, int]:
    m = _VERSION.match(str(text).strip())
    if not m:
        raise ValueError(f"not a version (X.Y.Z): {text!r}")
    return int(m[1]), int(m[2]), int(m[3])


def major(text: str) -> int:
    return parse(text)[0]
