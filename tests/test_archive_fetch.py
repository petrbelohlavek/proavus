"""archive_fetch.py with a fake network: fictional ARON answers, no real portal is contacted."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from helpers import ROOT

import archive_fetch as af

APU = "11111111-2222-4333-8444-555555555555"
DAO = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
FILES = [f"00000000-0000-4000-8000-00000000000{i}" for i in range(1, 4)]
JPEG = b"\xff\xd8\xff\xe0" + b"fictional image" * 10 + b"\xff\xd9"
ENTITY = {
    "id": APU, "name": "Matrika N 1870–1890, farnost Vzorkov (fictional)", "description": "test data",
    "parts": [{"type": "PT~ARCH~DESC", "items": [
        {"type": "UNIT~DATE", "value": "1870–1890", "visible": True},
        {"type": "OTHERID~SIG", "value": "Vzorkov 7", "visible": True},
        {"type": "STORAGE", "value": "hidden", "visible": False}]}],
    "digitalObjects": [{"id": DAO, "order": 1, "files": [
        {"id": FILES[i], "order": i + 1, "type": "PUBLISHED", "name": f"VZORKOV_7_{i + 1:05}.JPG", "contentType": "image/jpeg", "size": len(JPEG)}
        for i in range(3)] + [
        # ARON lists a thumbnail and a tile for every image, without name or size
        {"id": f"99999999-0000-4000-8000-0000000000{k}{i}", "order": i + 1, "type": kind, "name": None, "size": None}
        for k, kind in ((1, "THUMBNAIL"), (2, "TILE")) for i in range(3)]}],
}
BOOK_URL = f"https://aron.vychodoceskearchivy.cz/apu/{APU}"


class Response:
    def __init__(self, body: bytes, content_type="image/jpeg"):
        self.body, self.headers = body, {"Content-Type": content_type}

    def read(self, n=-1):
        return self.body if n < 0 else self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeNet:
    """Answers like ARON; records every URL asked for."""

    def __init__(self, images=None, entity=ENTITY):
        self.calls: list[str] = []
        self.images = images or {}
        self.entity = entity

    def __call__(self, url, method="GET"):
        self.calls.append(url)
        if url.endswith(f"/api/aron/apu/{APU}/entity"):
            return Response(json.dumps(self.entity).encode(), "application/json")
        fid = url.rsplit("/", 1)[-1]
        body, ctype = self.images.get(fid, (JPEG, "image/jpeg"))
        return Response(body, ctype)


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name) / "downloads"
        self.net = FakeNet()
        af.PAUSE_SECONDS = 0

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = af.main(list(args), fetch=self.net)
        return code, out.getvalue(), err.getvalue()


class AronBook(Case):
    def test_book(self):
        code, out, _ = self.run_cli("book", BOOK_URL)
        self.assertEqual(code, 0)
        self.assertIn("Matrika N 1870–1890, farnost Vzorkov (fictional)", out)
        self.assertIn("3 images", out)
        self.assertIn("OTHERID~SIG: Vzorkov 7", out)
        self.assertNotIn("hidden", out)

    def test_list_downloads_nothing(self):
        code, out, _ = self.run_cli("list", BOOK_URL, "--from", "2")
        self.assertEqual(code, 0)
        self.assertIn("VZORKOV_7_00002.JPG", out)
        self.assertNotIn("VZORKOV_7_00001.JPG", out)
        self.assertIn("2 of 3 images – nothing downloaded", out)   # thumbnails and tiles are not images
        self.assertNotIn("?", out)
        self.assertEqual(self.net.calls, [f"https://aron.vychodoceskearchivy.cz/api/aron/apu/{APU}/entity"])

    def test_link_to_the_viewer(self):
        code, out, _ = self.run_cli("link", BOOK_URL, "--image", "2")
        # the viewer opens an image by the ID of its tile (order 2 → …0021)
        self.assertEqual(out.strip(), f"{BOOK_URL}/dao/{DAO}/file/99999999-0000-4000-8000-000000000021")

    def test_bare_id(self):
        self.assertIsInstance(af.portal_for(APU, self.net), af.Aron)


class AronGet(Case):
    def test_dry_run_downloads_nothing(self):
        code, out, _ = self.run_cli("get", BOOK_URL, "--images", "1-2", "--out", str(self.out), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("would download     1", out)
        self.assertIn("nothing downloaded (dry run)", out)
        self.assertFalse(self.out.exists())
        self.assertEqual(len(self.net.calls), 1)       # only the list

    def test_get_checks_and_saves(self):
        code, out, err = self.run_cli("get", BOOK_URL, "--images", "1,3", "--out", str(self.out))
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["VZORKOV_7_00001.JPG", "VZORKOV_7_00003.JPG"])
        self.assertEqual((self.out / "VZORKOV_7_00001.JPG").read_bytes(), JPEG)
        self.assertIn(f"/api/aron/referencedfiles/{FILES[2]}", self.net.calls[-1])

    def test_existing_file_is_not_downloaded_again(self):
        self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out))
        calls = len(self.net.calls)
        self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out))
        self.assertEqual(len(self.net.calls), calls + 1)   # the list again, no image

    def test_at_most_max_images(self):
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "1-3", "--out", str(self.out), "--max", "2")
        self.assertEqual(code, 1)
        self.assertIn("3 images requested, at most 2 per call", err)
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out), "--max", "500")
        self.assertIn("--max must be between 1 and 50", err)

    def test_no_such_image(self):
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "7", "--out", str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("the book has 3 images; no image 7", err)

    def test_wrong_size_is_not_saved(self):
        self.net.images[FILES[0]] = (JPEG[:-10] + b"\xff\xd9", "image/jpeg")
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("bytes received", err)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_not_a_jpeg_is_not_saved(self):
        fake = b"<html>please log in</html>".ljust(len(JPEG), b" ")
        self.net.images[FILES[0]] = (fake, "image/jpeg")
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out))
        self.assertIn("not a complete JPEG", err)
        self.net.images[FILES[0]] = (JPEG, "text/html")
        code, _, err = self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(self.out))
        self.assertIn("not a JPEG", err)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_never_into_a_repository(self):
        for folder in (ROOT / "tmp-images", ROOT / "tests" / "fixtures" / "family" / "images"):
            code, _, err = self.run_cli("get", BOOK_URL, "--images", "1", "--out", str(folder), "--dry-run")
            self.assertEqual(code, 3, err)
            self.assertIn("inside a repository", err)
            self.assertFalse(folder.exists())


class ManualPortals(Case):
    MATRICULA = "https://data.matricula-online.eu/de/oesterreich/beispiel/vzorkov/01-01/"

    def test_matricula_link_only(self):
        code, out, _ = self.run_cli("link", self.MATRICULA, "--image", "41")
        self.assertEqual(out.strip(), self.MATRICULA + "?pg=41")
        for cmd in (("book", self.MATRICULA), ("list", self.MATRICULA),
                    ("get", self.MATRICULA, "--images", "41", "--out", str(self.out))):
            code, _, err = self.run_cli(*cmd)
            self.assertEqual(code, 3, cmd)
            self.assertIn("robots.txt", err)
        self.assertEqual(self.net.calls, [])     # Matricula is never contacted

    def test_acta_publica_link_only(self):
        code, out, _ = self.run_cli("link", "9999", "--image", "12")
        self.assertEqual(out.strip(), "https://www.mza.cz/actapublica/matrika/hledani?typ=signatura&mode=show&signatura=9999&strana=12")
        viewer = "https://www.mza.cz/actapublica/matrika/hledani?typ=signatura&mode=show&signatura=9999&strana=1"
        code, out, _ = self.run_cli("link", viewer, "--image", "30")
        self.assertIn("signatura=9999&strana=30", out)
        code, _, err = self.run_cli("get", viewer, "--images", "30", "--out", str(self.out))
        self.assertEqual(code, 3)
        self.assertIn("consent", err)
        self.assertEqual(self.net.calls, [])

    def test_acta_publica_viewer_link(self):
        """…/matrika/detail/<id>?image=<prefix>-<image × 10, five digits>.jp2 (research 2026-10-25)."""
        viewer = "https://www.mza.cz/actapublica/matrika/detail/1234?image=999000001-000002-000003-000000-000004-0-0001-00120.jp2"
        code, out, _ = self.run_cli("link", viewer, "--image", "250")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "https://www.mza.cz/actapublica/matrika/detail/1234?image=999000001-000002-000003-000000-000004-0-0001-02500.jp2")
        code, out, _ = self.run_cli("link", viewer, "--image", "7")
        self.assertTrue(out.strip().endswith("-00070.jp2"))
        code, _, err = self.run_cli("link", "https://www.mza.cz/actapublica/matrika/detail/1234", "--image", "7")
        self.assertEqual(code, 1)
        self.assertIn("copy the address of any image", err)
        self.assertEqual(self.net.calls, [])

    def test_unknown_portal(self):
        code, _, err = self.run_cli("book", "https://example.org/register/1")
        self.assertEqual(code, 1)
        self.assertIn("unknown portal", err)


class SourceAccess(Case):
    """--source: the URL and the access mode of a source in the family repository (ADR 0064)."""

    SRC = "SO-20261025-ab-s07"

    def add_source(self, **extra):
        repo = Path(self._tmp.name) / "family"
        (repo / "sources").mkdir(parents=True, exist_ok=True)
        lines = [f"id: {self.SRC}", "type: source", f"url: {BOOK_URL}"]
        lines += [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in extra.items()]
        (repo / "sources" / f"{self.SRC}.md").write_text("---\n" + "\n".join(lines) + "\n---\n", encoding="utf-8")
        return str(repo)

    def test_url_from_the_source(self):
        repo = self.add_source()
        code, out, _ = self.run_cli("book", "--source", self.SRC, "--repo", repo)
        self.assertEqual(code, 0)
        self.assertIn("3 images", out)

    def test_url_of_a_volume(self):
        other = "https://data.matricula-online.eu/de/oesterreich/beispiel/vzorkov/02-01/"
        repo = self.add_source(volumes=[{"volume": "II", "url": other}])
        code, out, _ = self.run_cli("link", "--source", self.SRC, "--volume", "ii", "--repo", repo, "--image", "2")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), other + "?pg=2")
        code, _, err = self.run_cli("link", "--source", self.SRC, "--volume", "IX", "--repo", repo, "--image", "2")
        self.assertEqual(code, 1)
        self.assertIn("has no volume 'IX'", err)

    def test_on_site_source_refuses_everything(self):
        repo = self.add_source(access={"mode": "on-site", "held_by": "registry-office", "note": "not digitised"})
        for cmd in (("book",), ("list",), ("link", "--image", "2"),
                    ("get", "--images", "1", "--out", str(self.out))):
            code, _, err = self.run_cli(cmd[0], "--source", self.SRC, "--repo", repo, *cmd[1:])
            self.assertEqual(code, 3, cmd)
            self.assertIn("access on-site, held by registry-office – not digitised", err)
        self.assertEqual(self.net.calls, [])       # the portal is never contacted
        self.assertFalse(self.out.exists())

    def test_link_mode_allows_only_links(self):
        repo = self.add_source(access={"mode": "link"})
        code, out, _ = self.run_cli("link", "--source", self.SRC, "--repo", repo, "--image", "2")
        self.assertEqual(code, 0)
        self.assertIn("/dao/", out)
        code, _, err = self.run_cli("get", "--source", self.SRC, "--repo", repo, "--images", "1", "--out", str(self.out), "--dry-run")
        self.assertEqual(code, 3)
        self.assertIn("'get' needs automated", err)

    def test_source_never_widens_the_portal(self):
        matricula = "https://data.matricula-online.eu/de/oesterreich/beispiel/vzorkov/01-01/"
        repo = self.add_source(url=matricula, access={"mode": "automated"})
        code, _, err = self.run_cli("list", "--source", self.SRC, "--repo", repo)
        self.assertEqual(code, 3)
        self.assertIn("robots.txt", err)
        self.assertEqual(self.net.calls, [])

    def test_missing_source_and_missing_url(self):
        code, _, err = self.run_cli("book", "--source", "SO-20261025-ab-xxx", "--repo", self._tmp.name)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)
        code, _, err = self.run_cli("book")
        self.assertEqual(code, 1)
        self.assertIn("give a book URL or --source", err)


class Catalogue(Case):
    """regions/*/portals.yaml – what the tool may do on each portal (ADR 0050)."""

    def test_regions_and_access(self):
        catalog = af.load_catalog()
        self.assertEqual(catalog["matricula"]["regions"], ["at", "cz"])
        self.assertEqual({k: v["access"] for k, v in catalog.items()}, {
            "matricula": "link", "friedhoefe-wien": "manual", "wstla": "manual", "anno": "manual",
            "lehmann": "manual", "aron": "automated", "acta-publica": "link", "digi-ceskearchivy": "manual"})

    def test_adapters_agree_with_the_code(self):
        catalog = af.load_catalog()
        for entry in catalog.values():
            cls = af.ADAPTERS.get(entry.get("adapter"))
            if cls is None:
                continue
            self.assertEqual(sorted(entry["hosts"]), sorted(cls.hosts), entry["id"])
            self.assertEqual(entry["access"], "automated" if cls.automated else "link", entry["id"])
            if not cls.automated:
                self.assertEqual(entry["why"], cls.why, entry["id"])
        self.assertEqual({e["adapter"] for e in catalog.values() if e.get("adapter")}, set(af.ADAPTERS))

    def test_manual_portal_refuses_everything(self):
        url = "https://www.friedhoefewien.at/verstorbenensuche?name=Pokusny"
        for cmd in (("book", url), ("list", url), ("link", url, "--image", "1"),
                    ("get", url, "--images", "1", "--out", str(self.out))):
            code, _, err = self.run_cli(*cmd)
            self.assertEqual(code, 3, cmd)
            self.assertIn("Search it yourself in the browser: https://www.friedhoefewien.at/", err)
            self.assertIn("burial date", err)
        self.assertEqual(self.net.calls, [])

    def test_portals_command(self):
        code, out, _ = self.run_cli("portals", "--region", "at")
        self.assertEqual(code, 0)
        self.assertIn("Friedhöfe Wien – Verstorbenensuche  [manual]", out)
        self.assertIn("aus gesetzlichen Gründen gesperrt", out)
        self.assertNotIn("ARON", out)
        self.assertNotIn("Registers of some Czech dioceses", out)   # cz note of Matricula
        code, out, _ = self.run_cli("portals")
        self.assertIn("(cz) Registers of some Czech dioceses", out)

    def write_region(self, region, entries):
        import yaml
        folder = Path(self._tmp.name) / "regions" / region
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "portals.yaml").write_text(yaml.safe_dump({"portals": entries}), encoding="utf-8")
        return folder.parent

    def test_regions_must_agree(self):
        entry = {"id": "x", "name": "X", "url": "https://x.example/", "hosts": ["x.example"], "access": "manual", "why": "w", "notes": ["a"]}
        self.write_region("aa", [entry])
        regions = self.write_region("bb", [{**entry, "notes": ["b"]}])
        self.assertEqual([n for _, n in af.load_catalog(regions)["x"]["notes"]], ["a", "b"])
        self.write_region("bb", [{**entry, "access": "link", "adapter": "matricula"}])
        with self.assertRaises(af.FetchError) as cm:
            af.load_catalog(regions)
        self.assertIn("differs from its entry in another region", str(cm.exception))

    def test_bad_entries(self):
        entry = {"id": "x", "name": "X", "url": "https://x.example/", "hosts": ["x.example"], "why": "w"}
        for bad, fragment in (({"access": "sometimes"}, "access must be one of"),
                              ({"access": "link"}, "name an adapter"),
                              ({"access": "manual", "adapter": "aron"}, "name an adapter"),
                              ({"access": "link", "adapter": "nope"}, "name an adapter")):
            regions = self.write_region("aa", [{**entry, **bad}])
            with self.assertRaises(af.FetchError) as cm:
                af.load_catalog(regions)
            self.assertIn(fragment, str(cm.exception))


class Helpers(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(af.parse_range("3"), [3])
        self.assertEqual(af.parse_range("3-5,8,4"), [3, 4, 5, 8])
        for bad in ("0", "5-3", "a", "3-x"):
            with self.assertRaises(af.FetchError):
                af.parse_range(bad)

    def test_jpeg_check(self):
        self.assertTrue(af.is_jpeg(JPEG))
        self.assertFalse(af.is_jpeg(JPEG[:-2]))
        self.assertFalse(af.is_jpeg(b"GIF89a"))

    def test_safe_file_names(self):
        self.assertEqual(af.safe_name("../../etc/passwd"), "passwd.jpg")
        self.assertEqual(af.safe_name("CZ 215/0001.JPG"), "0001.JPG")


if __name__ == "__main__":
    unittest.main()
