#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools==4.54.1", "uharfbuzz==0.41.0"]
# ///
"""Lettering of the logo as outlines (ADR 0056).

The logo files keep no <text>: the name and the subtitle are paths drawn from
the open font Gelasio (SIL OFL 1.1, metric-compatible with Georgia, which the
logo was designed in). This script redraws the group <g id="lettering"> in
every logo file from LETTERING below; the rest of each file stays as it is.

The font is not part of the repository. Get it once:
  https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf
  (version 1.008, sha256 below) and run
  uv run brand/lettering.py PATH/TO/Gelasio[wght].ttf
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_SHA256 = "4daecea457258c9ebeb8bc99ed3fd24353618bfad3ea4b93fa0b5d0468fc04e4"
BRAND = Path(__file__).resolve().parent
FILES = ["proavus-logo.svg", "proavus-logo-dark.svg", "proavus-social.svg"]
# text, x, y (baseline), font size, letter spacing – as designed in Georgia
LETTERING = [
    ("Proavus", 500, 346, 168, 2),
    ("Evidence-first genealogy with AI", 505, 415, 41.97, 0),
]
GROUP = re.compile(r'<g id="lettering"[^>]*>.*?</g>\n?|(?:<text\b[^>]*>.*?</text>\n?)+', re.S)
FILL = re.compile(r'<(?:text|g id="lettering")\b[^>]*\bfill="(#[0-9A-Fa-f]{6})"')


def outline(font: TTFont, blob: hb.Blob, text: str, x: float, y: float, size: float, spacing: float) -> str:
    face = hb.Face(blob)
    hb_font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    # Browsers turn ligatures off when letters are spaced.
    hb.shape(hb_font, buf, {"kern": True, "liga": spacing == 0})
    scale = size / font["head"].unitsPerEm
    glyphs = font.getGlyphSet()
    names = font.getGlyphOrder()
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    pen_x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        dx = x + (pen_x + pos.x_offset) * scale
        dy = y - pos.y_offset * scale
        glyphs[names[info.codepoint]].draw(TransformPen(pen, (scale, 0, 0, -scale, dx, dy)))
        pen_x += pos.x_advance + spacing / scale
    return pen.getCommands()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    font_path = Path(argv[0])
    data = font_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != FONT_SHA256:
        raise SystemExit(f"lettering: {font_path} is not Gelasio 1.008 (sha256 differs) – the outlines would change")
    font = TTFont(font_path)
    blob = hb.Blob(data)
    paths = [(text, outline(font, blob, *spec)) for spec in LETTERING for text in [spec[0]]]
    for name in FILES:
        svg = (BRAND / name).read_text(encoding="utf-8")
        fill = FILL.search(svg)
        if not fill or not GROUP.search(svg):
            raise SystemExit(f"lettering: {name} has no lettering to redraw")
        body = "".join(f'<path d="{d}"/>\n' for _, d in paths)
        group = (f'<g id="lettering" fill="{fill.group(1)}" aria-hidden="true">\n'
                 f'<!-- {" · ".join(t for t, _ in paths)} – Gelasio Regular (SIL OFL 1.1) as outlines -->\n'
                 f'{body}</g>\n')
        (BRAND / name).write_text(GROUP.sub(lambda _: group, svg, count=1), encoding="utf-8")
        print(f"lettering: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
