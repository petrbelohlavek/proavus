"""Grade: the page → image anchors break after an inserted sheet (ADR 0055, 0061)."""

from evalkit import Check, new

BOOK = "SO-20261024-ab-s05"


def true_image(page: int) -> int:
    """What the portal really shows: one image per page, an unnumbered sheet after page 60."""
    return page + 2 if page <= 60 else page + 3


def _int(value):
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def grade(before, after):
    records = [r for r in new(before, after, "record") if r.data.get("source") == BOOK
               and _int((r.data.get("locator") or {}).get("page")) == 80]
    loc = (records[0].data.get("locator") or {}) if records else {}
    image = _int(loc.get("image")) or _int(str(loc.get("url", "")).rstrip("/").rsplit("/", 1)[-1])
    src = after.entities.get(BOOK)
    anchors = [(_int(a.get("page")), _int(a.get("image"))) for m in (src.data.get("image_map") or [] if src else [])
               if isinstance(m, dict) for a in m.get("anchors") or [] if isinstance(a, dict)]
    false = [f"page {p} = image {i}" for p, i in anchors if p is not None and i != true_image(p)]
    return [
        Check("record-on-the-right-image", image == 83,
              f"record of page 80 names image {image}, the page is on image 83" if records else "no record of page 80"),
        Check("anchor-after-the-break", any(p is not None and p > 60 and i == true_image(p) for p, i in anchors),
              f"anchors of {BOOK}: {anchors}"),
        Check("no-false-anchor", not false, f"anchors that the images do not show: {', '.join(false)}"),
    ]
