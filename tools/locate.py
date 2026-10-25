#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Page → image: where a page or folio of a source is in the portal viewer.

Usage:  uv run tools/locate.py SOURCE_ID --page N [--volume V] [--part P] [--repo DIR]
        uv run tools/locate.py SOURCE_ID --folio 23r [--volume V] [--part P] [--repo DIR]

Computes the image from the anchors in the source's `image_map` (ADR 0061)
and says what the result rests on: exact (an anchor), interpolated (between
two anchors with a regular step), extrapolated (outside the anchors – only an
estimate) or a break (the anchors disagree – read a page in between and add
an anchor). Exit code 0 for exact or interpolated, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from proavuslib import imagemap  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402

HINT = {
    "exact": "an anchor",
    "interpolated": "between two anchors",
    "extrapolated": "outside the anchors – only an estimate; read the page on the image and add an anchor",
    "break": "the anchors disagree here – read a page in between and add an anchor",
    "no-map": "",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Page or folio → image of a source, from its image map (Proavus).")
    parser.add_argument("source", help="source ID (SO-…)")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--page", type=int)
    where.add_argument("--folio", help="folio with side, e.g. 23r")
    parser.add_argument("--volume", help="volume of the source")
    parser.add_argument("--part", help="part of the book with its own page numbering (ADR 0068)")
    parser.add_argument("--repo", default=".", help="family repository (default: .)")
    args = parser.parse_args(argv)

    v = RepoValidator(Path(args.repo).resolve(), TOOLS_DIR.parent)
    v.run()
    src = v.entities.get(args.source)
    if src is None or src.type != "source":
        print(f"locate: {args.source} is not a source in this repository", file=sys.stderr)
        return 2
    image_map = imagemap.map_for(src.data, args.volume, args.part)
    what = f"folio {args.folio}" if args.folio else f"page {args.page}"
    if image_map is None:
        vol = "".join(f" ({k} {x})" for k, x in (("volume", args.volume), ("part", args.part)) if x)
        print(f"{src.id}{vol} has no image map – read the page number on two images, far apart, and write them "
              "as anchors into image_map of the source")
        return 1
    problems = imagemap.problems(image_map)
    if problems:
        for msg in problems:
            print(f"image map of {src.id}: {msg}")
        return 1
    pos = imagemap.position(image_map, {"page": args.page, "folio": args.folio})
    if pos is None:
        print(f"the image map of {src.id} counts {imagemap.unit(image_map)}s – give --{imagemap.unit(image_map)}")
        return 1
    found = imagemap.locate(image_map, pos)
    rests = imagemap.describe(image_map, found)
    if found.image is None:
        print(f"{what}: no image – {HINT[found.status]} ({rests})")
    else:
        print(f"{what}: image {found.image} – {found.status}, {HINT[found.status]} ({rests})")
    vol = next((x for x in src.data.get("volumes") or [] if isinstance(x, dict) and args.volume is not None
                and str(x.get("volume")).strip().casefold() == str(args.volume).strip().casefold()), {})
    url = vol.get("url") or src.data.get("url")
    if found.image is not None and url:
        print(f"link: uv run .proavus/tools/archive_fetch.py link {url} --image {found.image}")
    return 0 if found.sure else 1


if __name__ == "__main__":
    sys.exit(main())
