"""Page (or folio) → image of a portal viewer, from anchors (ADR 0061).

An anchor is a page or folio number read on an image. Between two anchors
the image is computed only when the step is regular: k images per page
(k = 0, 1, 2 …) or m pages per image. Otherwise the anchors disagree – there
is a break between them (inserted sheet, missing or double scan) and another
anchor is needed. Outside the anchors the result is only an estimate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FOLIO = re.compile(r"^\s*([0-9]+)\s*([rv])\s*$")


@dataclass
class Located:
    image: int | None
    status: str                 # exact · interpolated · extrapolated · break · no-map
    low: dict | None = None     # the anchors used
    high: dict | None = None

    @property
    def sure(self) -> bool:
        return self.status in ("exact", "interpolated")


def folio_position(folio) -> int | None:
    """23r → 45, 23v → 46: the side as a running number."""
    m = FOLIO.match(str(folio))
    if not m:
        return None
    n = int(m.group(1))
    return 2 * n - 1 if m.group(2) == "r" else 2 * n


def as_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def unit(image_map: dict) -> str:
    return image_map.get("unit") or "page"


def position(image_map: dict, item: dict) -> int | None:
    """Position of an anchor or a locator in the map's unit (page number or folio side)."""
    if unit(image_map) == "folio":
        return folio_position(item.get("folio")) if item.get("folio") is not None else None
    return as_int(item.get("page"))


def anchors(image_map: dict) -> list[tuple[int, int, dict]]:
    """(position, image, anchor) sorted by position; anchors without a usable position are left out."""
    out = []
    for a in image_map.get("anchors") or []:
        if not isinstance(a, dict):
            continue
        pos, img = position(image_map, a), as_int(a.get("image"))
        if pos is not None and img is not None:
            out.append((pos, img, a))
    return sorted(out, key=lambda x: x[0])


def problems(image_map: dict) -> list[str]:
    """Anchors that cannot all be true: the same position twice, or images going back."""
    out = []
    pts = anchors(image_map)
    if len(pts) < len([a for a in image_map.get("anchors") or [] if isinstance(a, dict)]):
        out.append(f"an anchor has no {unit(image_map)} – this map counts {unit(image_map)}s")
    for (p1, i1, _), (p2, i2, _) in zip(pts, pts[1:]):
        if p1 == p2:
            out.append(f"two anchors at {_label(image_map, p1)}")
        elif i2 < i1:
            out.append(f"{_label(image_map, p2)} is on image {i2}, before image {i1} of {_label(image_map, p1)} – images go back")
    return out


def _label(image_map: dict, pos: int) -> str:
    if unit(image_map) == "folio":
        return f"folio {(pos + 1) // 2}{'r' if pos % 2 else 'v'}"
    return f"page {pos}"


def _step(p1: int, i1: int, p2: int, i2: int, pos: int) -> int | None:
    """Image at pos on the line through two anchors, if the step is regular."""
    dp, di = p2 - p1, i2 - i1
    if dp == 0:
        return None
    if di % dp == 0:
        return i1 + (pos - p1) * (di // dp)
    if di > 0 and dp % di == 0:
        return i1 + (pos - p1) // (dp // di)
    return None


def locate(image_map: dict, pos: int) -> Located:
    pts = anchors(image_map)
    if len(pts) < 2:
        return Located(None, "no-map")
    for p, i, a in pts:
        if p == pos:
            return Located(i, "exact", a, a)
    if pts[0][0] < pos < pts[-1][0]:
        for (p1, i1, a1), (p2, i2, a2) in zip(pts, pts[1:]):
            if p1 < pos < p2:
                img = _step(p1, i1, p2, i2, pos)
                return Located(img, "interpolated" if img is not None else "break", a1, a2)
    (p1, i1, a1), (p2, i2, a2) = (pts[0], pts[1]) if pos < pts[0][0] else (pts[-2], pts[-1])
    img = _step(p1, i1, p2, i2, pos)
    return Located(img if img is None or img >= 1 else None, "extrapolated" if img is not None else "break", a1, a2)


def _volume_key(value) -> str:
    return str(value).strip().casefold()


def map_for(source: dict, volume=None) -> dict | None:
    """The image map of the source for this volume (or the map without a volume)."""
    maps = [m for m in source.get("image_map") or [] if isinstance(m, dict)]
    if volume is not None:
        same = [m for m in maps if m.get("volume") is not None and _volume_key(m["volume"]) == _volume_key(volume)]
        if same:
            return same[0]
    general = [m for m in maps if m.get("volume") is None]
    return general[0] if general else None


def locate_in_source(source: dict, page=None, folio=None, volume=None) -> Located:
    image_map = map_for(source, volume)
    if image_map is None:
        return Located(None, "no-map")
    pos = position(image_map, {"page": page, "folio": folio})
    if pos is None:
        return Located(None, "no-map")
    return locate(image_map, pos)


def describe(image_map: dict, located: Located) -> str:
    """The anchors a result rests on, in words."""
    if located.low is None:
        return ""
    def one(a):
        return f"{_label(image_map, position(image_map, a))} = image {a.get('image')}"
    return one(located.low) if located.low is located.high else f"{one(located.low)}, {one(located.high)}"
