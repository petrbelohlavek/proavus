"""Page → image from anchors (proavuslib.imagemap, tools/locate.py, ADR 0061)."""

from __future__ import annotations

import contextlib
import io
import unittest

from helpers import FamilyRepoCase, ROOT, TODAY  # noqa: F401  (adds tools/ to sys.path)

import locate  # noqa: E402
from proavuslib import imagemap  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402

SRC = "SO-20261020-ab-s01"
REC = "R-20261020-ab-r01"       # page 41, folio 21r, image 44 (from its URL)


def anchor(image, page=None, folio=None):
    a = {"image": image, "by": "ab", "on": "2026-10-24"}
    if page is not None:
        a["page"] = page
    if folio is not None:
        a["folio"] = folio
    return a


class Locate(unittest.TestCase):
    def test_one_page_per_image(self):
        m = {"anchors": [anchor(8, page=12), anchor(136, page=140)]}
        self.assertEqual(imagemap.locate(m, 50).image, 46)
        self.assertEqual(imagemap.locate(m, 50).status, "interpolated")
        self.assertEqual(imagemap.locate(m, 12).status, "exact")

    def test_two_pages_per_image(self):
        m = {"anchors": [anchor(8, page=12), anchor(122, page=240)]}   # pages 12–13 on image 8, 14–15 on 9 …
        self.assertEqual(imagemap.locate(m, 13).image, 8)
        self.assertEqual(imagemap.locate(m, 14).image, 9)
        self.assertEqual(imagemap.locate(m, 239).image, 121)

    def test_break_between_anchors(self):
        m = {"anchors": [anchor(8, page=12), anchor(125, page=240)]}   # 228 pages on 117 images: not regular
        found = imagemap.locate(m, 100)
        self.assertEqual((found.image, found.status), (None, "break"))

    def test_a_third_anchor_splits_the_book(self):
        # inserted sheet after page 240: two more images
        m = {"anchors": [anchor(8, page=12), anchor(122, page=240), anchor(124, page=241), anchor(154, page=301)]}
        self.assertEqual(imagemap.problems(m), [])
        self.assertEqual(imagemap.locate(m, 270).image, 138)
        self.assertEqual(imagemap.locate(m, 100).image, 52)

    def test_outside_the_anchors_is_an_estimate(self):
        m = {"anchors": [anchor(8, page=12), anchor(136, page=140)]}
        found = imagemap.locate(m, 150)
        self.assertEqual((found.image, found.status, found.sure), (146, "extrapolated", False))

    def test_folios(self):
        m = {"unit": "folio", "anchors": [anchor(5, folio="1r"), anchor(44, folio="40r")]}   # one image per leaf
        self.assertEqual(imagemap.folio_position("21r"), 41)
        self.assertEqual(imagemap.folio_position("21v"), 42)
        self.assertEqual(imagemap.locate(m, imagemap.folio_position("21r")).image, 25)
        self.assertEqual(imagemap.locate(m, imagemap.folio_position("21v")).image, 25)

    def test_problems(self):
        self.assertIn("two anchors at page 12", imagemap.problems({"anchors": [anchor(8, page=12), anchor(9, page=12)]})[0])
        self.assertIn("images go back", imagemap.problems({"anchors": [anchor(8, page=12), anchor(5, page=20)]})[0])
        self.assertIn("this map counts folios", imagemap.problems({"unit": "folio", "anchors": [anchor(8, page=12), anchor(9, folio="3r")]})[0])

    def test_map_per_volume(self):
        src = {"image_map": [{"anchors": [anchor(1, page=1), anchor(10, page=10)]},
                             {"volume": "II", "anchors": [anchor(3, page=1), anchor(12, page=10)]}]}
        self.assertEqual(imagemap.locate_in_source(src, page=5).image, 5)
        self.assertEqual(imagemap.locate_in_source(src, page=5, volume="ii").image, 7)
        self.assertEqual(imagemap.locate_in_source(src, page=5, volume="III").image, 5)   # falls back to the general map


    def test_map_per_part(self):
        """ADR 0068: parts of a book with their own page numbering – one map per part."""
        src = {"image_map": [{"anchors": [anchor(1, page=1), anchor(10, page=10)]},
                             {"part": "Ukázkov", "anchors": [anchor(120, page=1), anchor(129, page=10)]}]}
        self.assertEqual(imagemap.locate_in_source(src, page=5).image, 5)
        self.assertEqual(imagemap.locate_in_source(src, page=5, part="ukázkov").image, 124)
        self.assertEqual(imagemap.locate_in_source(src, page=5, part="Vzorkov").status, "no-map")   # never another part's map


class Validate(FamilyRepoCase):
    def set_map(self, *anchors, **extra):
        self.edit(SRC, lambda d: d.update(image_map=[{"anchors": list(anchors), **extra}]))

    def test_record_fits_the_map(self):
        self.set_map(anchor(4, page=1), anchor(84, page=81))     # offset 3
        self.edit(REC, lambda d: d["locator"].update(image=44))
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("image map", "\n".join(report.warnings))

    def test_record_does_not_fit_the_map(self):
        self.set_map(anchor(4, page=1), anchor(84, page=81))
        self.edit(REC, lambda d: d["locator"].update(image=46))
        self.assertWarning(self.validate(), "locator image 46, but the image map of SO-20261020-ab-s01 gives image 44 for page 41 "
                                            "(page 1 = image 4, page 81 = image 84)")

    def test_folio_map(self):
        self.set_map(anchor(5, folio="1r"), anchor(44, folio="40r"), unit="folio")
        self.edit(REC, lambda d: d["locator"].update(image=30))
        self.assertWarning(self.validate(), "gives image 25 for folio 21r")

    def test_estimate_is_not_checked(self):
        self.set_map(anchor(4, page=1), anchor(14, page=11))
        self.edit(REC, lambda d: d["locator"].update(image=99))
        self.assertNotIn("image map", "\n".join(self.validate().warnings))

    def test_anchors_that_disagree(self):
        self.set_map(anchor(8, page=12), anchor(5, page=20))
        self.assertError(self.validate(), "image_map: page 20 is on image 5, before image 8 of page 12 – images go back")

    def test_one_anchor_is_not_a_map(self):
        self.set_map(anchor(8, page=12))
        self.assertError(self.validate(), "anchors")

    def test_anchor_needs_who_and_when(self):
        self.set_map({"page": 12, "image": 8}, anchor(9, page=13))
        self.assertError(self.validate(), "'by' is a required property")

    def test_map_of_an_unknown_volume(self):
        self.edit(SRC, lambda d: d.update(volumes=[{"volume": "I"}]))
        self.edit(REC, lambda d: d["locator"].update(volume="I"))
        self.set_map(anchor(4, page=1), anchor(84, page=81), volume="IX")
        self.assertError(self.validate(), "image_map of volume 'IX': volume 'IX' is not one of the volumes of the source")

    def test_two_maps_for_one_volume(self):
        self.edit(SRC, lambda d: d.update(image_map=[{"anchors": [anchor(4, page=1), anchor(84, page=81)]},
                                                     {"anchors": [anchor(4, page=1), anchor(84, page=81)]}]))
        self.assertError(self.validate(), "two image maps for the whole source")

    def test_two_maps_for_one_part(self):
        part = {"part": "Ukázkov", "anchors": [anchor(120, page=1), anchor(129, page=10)]}
        self.edit(SRC, lambda d: d.update(image_map=[{"anchors": [anchor(4, page=1), anchor(84, page=81)]}, part]))
        self.assertClean(self.validate())
        self.edit(SRC, lambda d: d.update(image_map=[part, part]))
        self.assertError(self.validate(), "two image maps for part 'Ukázkov'")

    def test_cli_part(self):
        self.edit(SRC, lambda d: d.update(image_map=[{"part": "Ukázkov", "anchors": [anchor(120, page=1), anchor(129, page=10)]}]))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = locate.main([SRC, "--page", "5", "--part", "Ukázkov", "--repo", str(self.repo)])
        self.assertEqual(code, 0)
        self.assertIn("page 5: image 124 – interpolated", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = locate.main([SRC, "--page", "5", "--repo", str(self.repo)])
        self.assertEqual(code, 1)
        self.assertIn("has no image map", out.getvalue())

    def test_cli(self):
        self.set_map(anchor(4, page=1), anchor(84, page=81))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = locate.main([SRC, "--page", "41", "--repo", str(self.repo)])
        self.assertEqual(code, 0)
        self.assertIn("page 41: image 44 – interpolated", out.getvalue())
        self.assertIn("archive_fetch.py link https://example.org/archive/vzorkov-7 --image 44", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = locate.main([SRC, "--page", "120", "--repo", str(self.repo)])
        self.assertEqual(code, 1)
        self.assertIn("extrapolated", out.getvalue())

    def test_cli_without_a_map(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = locate.main([SRC, "--page", "41", "--repo", str(self.repo)])
        self.assertEqual(code, 1)
        self.assertIn("has no image map", out.getvalue())


if __name__ == "__main__":
    unittest.main()
