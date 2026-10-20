#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Book metadata, image lists and image downloads from archive portals (ADR 0041).

Usage:
  archive_fetch.py book URL              metadata of a book (register)
  archive_fetch.py list URL [--from N] [--to M]
                                         images with their size – downloads nothing
  archive_fetch.py link URL --image N    link to image N in the portal's viewer
  archive_fetch.py get URL --images 3-5 --out DIR [--dry-run] [--max N]
                                         download images into DIR (outside any
                                         repository); --dry-run lists what would
                                         be downloaded; at most --max (default 10)

Portals:
  ARON (ARchiv ONline, Východočeské archivy) – book, list, link, get through
      its public interface.
  Matricula Online, Acta Publica (MZA) – link only. Their operators do not
      allow automated access to the images (robots.txt, terms of use), so this
      tool never fetches anything from them: open the link and save the image
      yourself.

Downloading needs the user's explicit yes to the list from --dry-run
(/proavus:start). Full images never go into the family repository – only
small crops (records/evidence/). Exit codes: 0 ok, 1 error, 3 not allowed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "Proavus-archive-fetch (personal genealogical research; https://github.com/petrbelohlavek/proavus)"
DEFAULT_MAX, HARD_MAX = 10, 50           # images per call
MAX_IMAGE_BYTES = 40 * 1024 * 1024       # one image larger than this is refused
PAUSE_SECONDS = 1.0                      # between downloads – be gentle with the archive
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


class FetchError(Exception):
    pass


class NotAllowed(FetchError):
    pass


@dataclass
class Image:
    order: int
    name: str
    size: int | None
    content_type: str | None
    url: str


def http_get(url: str, method: str = "GET"):
    """Open a URL; returns the response (a file-like object with .headers). Tests replace it."""
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    return urllib.request.urlopen(request, timeout=60)  # noqa: S310 – only https URLs of known portals


# ------------------------------------------------------------------ ARON
class Aron:
    name = "ARON (Východočeské archivy)"
    hosts = ("aron.vychodoceskearchivy.cz",)
    automated = True

    def __init__(self, url: str, fetch=http_get):
        m = re.search(rf"/apu/({UUID})", url) or re.fullmatch(rf"({UUID})", url)
        if not m:
            raise FetchError(f"no ARON record ID (…/apu/<uuid>) in {url!r}")
        self.base = "https://aron.vychodoceskearchivy.cz"
        self.apu = m.group(1)
        self.fetch = fetch
        self._entity = None

    def entity(self) -> dict:
        if self._entity is None:
            with self.fetch(f"{self.base}/api/aron/apu/{self.apu}/entity") as response:
                self._entity = json.loads(response.read().decode("utf-8"))
        return self._entity

    def book(self) -> dict:
        e = self.entity()
        fields: dict[str, list[str]] = {}
        for part in e.get("parts") or []:
            for item in part.get("items") or []:
                if item.get("visible") is False or item.get("value") in (None, ""):
                    continue
                fields.setdefault(item.get("type", "?"), []).append(str(item["value"]))
        images = self.images()
        return {"portal": self.name, "id": self.apu, "url": f"{self.base}/apu/{self.apu}", "title": e.get("name"),
                "description": e.get("description"), "fields": fields, "images": len(images),
                "total_bytes": sum(i.size or 0 for i in images)}

    def _objects(self) -> list[dict]:
        return sorted(self.entity().get("digitalObjects") or [], key=lambda d: d.get("order") or 0)

    @staticmethod
    def _published(dao: dict) -> list[dict]:
        """The images themselves – the list also holds a THUMBNAIL and TILE file for each."""
        files = [f for f in dao.get("files") or [] if f.get("type", "PUBLISHED") == "PUBLISHED"]
        return sorted(files, key=lambda f: f.get("order") or 0)

    def images(self) -> list[Image]:
        out, n = [], 0
        for dao in self._objects():
            for f in self._published(dao):
                n += 1
                out.append(Image(n, str(f.get("name") or f.get("id")), f.get("size"), f.get("contentType"),
                                 f"{self.base}/api/aron/referencedfiles/{f['id']}"))
        return out

    def link(self, n: int) -> str:
        """The viewer opens an image by the ID of its TILE file (checked 2026-10-20), else by the image's own."""
        for dao in self._objects():
            files = self._published(dao)
            if n <= len(files):
                order = files[n - 1].get("order")
                tile = next((f for f in dao.get("files") or [] if f.get("type") == "TILE" and f.get("order") == order), None)
                return f"{self.base}/apu/{self.apu}/dao/{dao['id']}/file/{(tile or files[n - 1])['id']}"
            n -= len(files)
        raise FetchError("no such image in this book")


# ------------------------------------------------- portals without automation
class Manual:
    """A portal whose operator does not allow automated access to the images: links only."""
    automated = False
    why = ""

    def __init__(self, url: str, fetch=http_get):
        self.url = url

    def refuse(self, what: str):
        raise NotAllowed(f"{self.name}: {what} is not done automatically – {self.why}. Open the link "
                         f"(`archive_fetch.py link URL --image N`) and save the image yourself.")

    def book(self):
        self.refuse("reading the book")

    def images(self):
        self.refuse("listing the images")


class Matricula(Manual):
    name = "Matricula Online"
    hosts = ("data.matricula-online.eu",)
    why = "its robots.txt forbids automated access to the image pages (?pg=) and blocks AI agents"

    def link(self, n: int) -> str:
        parts = urllib.parse.urlsplit(self.url)
        if not re.search(r"/[a-z]{2}/.+/.+", parts.path):
            raise FetchError(f"not a Matricula book URL: {self.url!r} (expected https://data.matricula-online.eu/<lang>/…/<book>/)")
        path = parts.path if parts.path.endswith("/") else parts.path + "/"
        return urllib.parse.urlunsplit(("https", parts.netloc, path, f"pg={n}", ""))


class ActaPublica(Manual):
    name = "Acta Publica (Moravský zemský archiv)"
    hosts = ("www.mza.cz", "mza.cz")
    why = "its terms of use and robots.txt do not allow automated access without the archive's consent"

    def link(self, n: int) -> str:
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.url).query))
        book = query.get("signatura") or (self.url if re.fullmatch(r"[\w./ -]+", self.url) and "/" not in self.url else None)
        if not book:
            raise FetchError("give the Acta Publica book as a viewer URL with signatura=… or as the book number")
        q = urllib.parse.urlencode({"typ": "signatura", "mode": "show", "signatura": book, "strana": n})
        return f"https://www.mza.cz/actapublica/matrika/hledani?{q}"


PORTALS = (Aron, Matricula, ActaPublica)


def portal_for(url: str, fetch=http_get):
    host = urllib.parse.urlsplit(url).netloc.lower()
    for cls in PORTALS:
        if host in cls.hosts:
            return cls(url, fetch)
    if re.fullmatch(UUID, url):
        return Aron(url, fetch)
    if re.fullmatch(r"[\w.-]+", url):
        return ActaPublica(url, fetch)     # a bare book number (signatura)
    raise FetchError(f"unknown portal for {url!r} – supported: {', '.join(c.name for c in PORTALS)}")


# ------------------------------------------------------------------ download
def parse_range(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        a, _, b = part.strip().partition("-")
        if not a.isdigit() or (b and not b.isdigit()):
            raise FetchError(f"image numbers must look like 3, 3-5 or 3-5,8 – got {text!r}")
        lo, hi = int(a), int(b or a)
        if lo < 1 or hi < lo:
            raise FetchError(f"bad image range {part!r}")
        out += range(lo, hi + 1)
    return list(dict.fromkeys(out))


def check_target(out: Path) -> Path:
    """Downloads go to a folder outside any repository (full images never into git)."""
    out = out.expanduser().resolve()
    for folder in [out, *out.parents]:
        for marker in (".git", "repo.yaml", ".claude-plugin"):
            if (folder / marker).exists():
                raise NotAllowed(f"{out} is inside a repository ({folder}) – full images never go into git; "
                                 "choose a folder outside it (only small crops go into records/evidence/)")
    return out


def is_jpeg(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff" and data.rstrip(b"\x00")[-2:] == b"\xff\xd9"


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w.-]+", "_", Path(name).name).strip("._") or "image"
    return name if name.lower().endswith((".jpg", ".jpeg")) else name + ".jpg"


def select(images: list[Image], numbers: list[int], limit: int) -> list[Image]:
    if limit < 1 or limit > HARD_MAX:
        raise FetchError(f"--max must be between 1 and {HARD_MAX}")
    if len(numbers) > limit:
        raise FetchError(f"{len(numbers)} images requested, at most {limit} per call – split the range")
    by_order = {i.order: i for i in images}
    missing = [n for n in numbers if n not in by_order]
    if missing:
        raise FetchError(f"the book has {len(images)} images; no image {', '.join(map(str, missing))}")
    return [by_order[n] for n in numbers]


def download(portal, chosen: list[Image], out: Path, fetch=http_get, pause: float = PAUSE_SECONDS) -> list[Path]:
    out = check_target(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for k, image in enumerate(chosen):
        if image.size is not None and image.size > MAX_IMAGE_BYTES:
            raise FetchError(f"image {image.order} is {image.size} bytes – larger than the limit {MAX_IMAGE_BYTES}")
        target = out / safe_name(image.name)
        if target.is_file() and image.size is not None and target.stat().st_size == image.size:
            written.append(target)             # already here, same size
            continue
        if k:
            time.sleep(pause)
        with fetch(image.url) as response:
            ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise FetchError(f"image {image.order} is larger than the limit {MAX_IMAGE_BYTES} bytes")
        if ctype and ctype != "image/jpeg":
            raise FetchError(f"image {image.order}: the archive sent {ctype}, not a JPEG – nothing saved")
        if image.size is not None and len(data) != image.size:
            raise FetchError(f"image {image.order}: {len(data)} bytes received, {image.size} expected – nothing saved")
        if not is_jpeg(data):
            raise FetchError(f"image {image.order}: the file is not a complete JPEG – nothing saved")
        part = target.with_suffix(target.suffix + ".part")
        part.write_bytes(data)
        part.replace(target)
        written.append(target)
    return written


# ------------------------------------------------------------------ CLI
def human_size(n: int | None) -> str:
    if n is None:
        return "?"
    for unit in ("B", "kB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def main(argv: list[str] | None = None, fetch=http_get) -> int:
    parser = argparse.ArgumentParser(description="Book metadata, image lists and downloads from archive portals (Proavus).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("book", "list", "link", "get"):
        p = sub.add_parser(name)
        p.add_argument("url", help="book URL (or ARON record ID, Acta Publica book number)")
        if name == "list":
            p.add_argument("--from", dest="first", type=int, default=1)
            p.add_argument("--to", dest="last", type=int)
        if name == "link":
            p.add_argument("--image", type=int, required=True)
        if name == "get":
            p.add_argument("--images", required=True, help="e.g. 41 or 40-42 or 40-42,57")
            p.add_argument("--out", required=True, help="folder OUTSIDE the family repository")
            p.add_argument("--dry-run", action="store_true", help="only list what would be downloaded")
            p.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"at most this many images (default {DEFAULT_MAX}, limit {HARD_MAX})")
        p.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    try:
        portal = portal_for(args.url, fetch)
        if args.cmd == "link":
            print(portal.link(args.image))
            return 0
        if args.cmd == "book":
            info = portal.book()
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                print(f"{info['title']}\n{info['portal']} · {info['url']}\n{info['images']} images, {human_size(info['total_bytes'])}")
                for key, values in info["fields"].items():
                    print(f"  {key}: {'; '.join(values)}")
            return 0
        images = portal.images()
        if args.cmd == "list":
            shown = [i for i in images if i.order >= args.first and (args.last is None or i.order <= args.last)]
            if args.json:
                print(json.dumps([i.__dict__ for i in shown], ensure_ascii=False, indent=2))
            else:
                for i in shown:
                    print(f"{i.order:5}  {human_size(i.size):>9}  {i.name}")
                print(f"{len(shown)} of {len(images)} images – nothing downloaded")
            return 0
        chosen = select(images, parse_range(args.images), args.max)
        out = check_target(Path(args.out))
        total = sum(i.size or 0 for i in chosen)
        if args.dry_run:
            for i in chosen:
                print(f"would download {i.order:5}  {human_size(i.size):>9}  {i.name}  →  {out / safe_name(i.name)}")
            print(f"{len(chosen)} images, {human_size(total)} – nothing downloaded (dry run)")
            return 0
        written = download(portal, chosen, out, fetch)
        for path in written:
            print(f"saved {path} ({human_size(path.stat().st_size)})")
        print(f"{len(written)} images in {out}")
        return 0
    except NotAllowed as exc:
        print(f"archive_fetch: {exc}", file=sys.stderr)
        return 3
    except (FetchError, OSError, ValueError) as exc:
        print(f"archive_fetch: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
