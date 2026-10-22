#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools==4.54.1", "uharfbuzz==0.41.0"]
# ///
"""Lettering of the README picture as outlines (ADR 0057).

architecture.py runs on plain Python without fonts, so the words of the
picture are drawn here once and kept in lettering.json: per word its path,
starting at x 0 on the baseline, and its width (the sum of the advances,
with kerning, as a browser sets it). architecture.py centres and places them.

The fonts are not part of the repository. Get them once:
  Gelasio Regular 1.008 (SIL OFL 1.1, metric-compatible with Georgia), the
  same file as brand/lettering.py:
  https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf
  DejaVu Sans Mono 2.37 (Bitstream Vera licence, DejaVu changes public
  domain), ttf/DejaVuSansMono.ttf in
  https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip
and run
  uv run docs/images/lettering.py PATH/TO/Gelasio[wght].ttf PATH/TO/DejaVuSansMono.ttf
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "brand"))
from lettering import FONT_SHA256 as SERIF_SHA256, outline  # noqa: E402  (one way of drawing text, ADR 0056)

MONO_SHA256 = "b4a6c3e4faab8773f4ff761d56451646409f29abedd68f05d38c2df667d3c582"
# word, font ("serif" Gelasio / "mono" DejaVu Sans Mono), font size – as architecture.py uses them
WORDS = [
    ("Proavus", "serif", 54),
    ("proavus-novak", "mono", 19),
    ("proavus-smith", "mono", 19),
    ("proavus-muller", "mono", 19),
]


def width(blob: hb.Blob, font: TTFont, text: str, size: float) -> float:
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb.Font(hb.Face(blob)), buf, {"kern": True})
    return sum(pos.x_advance for pos in buf.glyph_positions) * size / font["head"].unitsPerEm


def load(path: str, sha256: str, name: str) -> tuple[TTFont, hb.Blob]:
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise SystemExit(f"lettering: {path} is not {name} (sha256 differs) – the outlines would change")
    return TTFont(path), hb.Blob(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    fonts = {"serif": load(argv[0], SERIF_SHA256, "Gelasio 1.008"),
             "mono": load(argv[1], MONO_SHA256, "DejaVu Sans Mono 2.37")}
    words = {}
    for text, kind, size in WORDS:
        font, blob = fonts[kind]
        words[text] = {"d": outline(font, blob, text, 0, 0, size, 0),
                       "width": round(width(blob, font, text, size), 2)}
    (HERE / "lettering.json").write_text(json.dumps(words, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"lettering: {len(words)} words in lettering.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
