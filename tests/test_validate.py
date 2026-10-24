"""validate.py on the fictional family repository: one test per rule."""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from helpers import FamilyRepoCase, ROOT, TODAY
from proavuslib.validator import RepoValidator

REC = "R-20261020-ab-r01"
SRC = "SO-20261020-ab-s01"
MATEJ = "P-20261020-ab-m01"
ANNA = "P-20261020-ab-a01"
JOSEF = "P-20261020-ab-j01"
ID_FATHER = "A-20261020-ab-i01"
REL = "RL-20261020-ab-f01"


class ValidFixture(FamilyRepoCase):
    def test_fixture_is_clean(self):
        report = self.validate()
        self.assertClean(report)
        self.assertEqual(report.warnings, [])
        self.assertEqual(report.files, 37)

    def test_cli_exit_code(self):
        ok = subprocess.run([sys.executable, str(ROOT / "tools/validate.py"), str(self.repo)], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        (self.repo / "repo.yaml").unlink()
        bad = subprocess.run([sys.executable, str(ROOT / "tools/validate.py"), str(self.repo)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("not a Proavus family repository", bad.stdout)


class RepoConfig(FamilyRepoCase):
    def test_missing_repo_yaml(self):
        (self.repo / "repo.yaml").unlink()
        self.assertError(self.validate(), "repo.yaml: missing")

    def test_unknown_extension(self):
        text = self.path("repo.yaml").read_text().replace("extensions: [cz]", "extensions: [xx]")
        self.path("repo.yaml").write_text(text)
        self.assertError(self.validate(), "extension 'xx' not found")


    def test_map_root_must_be_a_person(self):
        text = (self.repo / "repo.yaml").read_text(encoding="utf-8")
        (self.repo / "repo.yaml").write_text(text.replace("root: P-20261020-ab-n01", f"root: {REL}"), encoding="utf-8")
        self.assertError(self.validate(), "map.root")
        (self.repo / "repo.yaml").write_text(text.replace("root: P-20261020-ab-n01", "root: P-20261020-ab-zzz"), encoding="utf-8")
        self.assertError(self.validate(), "map.root: P-20261020-ab-zzz is not a person")

    def test_unknown_map_setting_is_an_error(self):
        with open(self.repo / "repo.yaml", "a", encoding="utf-8") as f:
            f.write("  colour: red\n")
        self.assertError(self.validate(), "repo.yaml", "colour")

class Headers(FamilyRepoCase):
    def test_missing_header(self):
        self.path("people/P-20261020-ab-x01.md").write_text("no header\n")
        self.assertError(self.validate(), "missing YAML header")

    def test_unknown_field_is_an_error(self):
        self.edit(MATEJ, lambda d: d.update(nickname="Matty"))
        self.assertError(self.validate(), "Unevaluated properties are not allowed")

    def test_regional_field_needs_extension(self):
        text = self.path("repo.yaml").read_text().replace("extensions: [cz]\n", "")
        self.path("repo.yaml").write_text(text)
        report = self.validate()
        self.assertError(report, "house_number")

    def test_unknown_vocabulary_value_only_warns(self):
        self.edit(REC, lambda d: d["participants"][3].update(role="best-man"))
        report = self.validate()
        self.assertClean(report)
        self.assertWarning(report, "unknown value 'best-man' in vocabulary participant_roles")

    def test_invalid_edtf_date(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1910-13"))
        self.assertError(self.validate(), "is not a 'edtf'")

    def test_unquoted_year_is_accepted(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date=1910))
        self.assertClean(self.validate())

    def test_schema_gap_is_reported_not_blocking(self):
        self.edit(MATEJ, lambda d: d.update(schema_gap=["served in the fire brigade – no fact type yet"]))
        report = self.validate()
        self.assertClean(report)
        self.assertTrue(any("fire brigade" in n for n in report.notes))

    def test_question_answered_needs_conclusion(self):
        self.edit("Q-20261020-ab-q01", lambda d: d.update(status="answered"))
        self.assertError(self.validate(), "'conclusion' is a required property")


class IdsAndFiles(FamilyRepoCase):
    def test_bad_id_format(self):
        self.edit(ANNA, lambda d: d.update(id="P-2026-ab-a01"))
        self.assertError(self.validate(), "does not match")

    def test_file_name_must_match_id(self):
        self.find(ANNA).rename(self.repo / "people" / "anna.md")
        self.assertError(self.validate(), "file name must be P-20261020-ab-a01.md")

    def test_slug_in_file_name_is_allowed(self):
        self.find(ANNA).rename(self.repo / "people" / "P-20261020-ab-a01--anna-vzorna.md")
        self.assertClean(self.validate())

    def test_duplicate_id(self):
        self.add("people/P-20261020-ab-a01--copy.md", {"id": ANNA, "type": "person", "names": [{"value": "X", "name_type": "birth"}], "vital_status": "deceased"})
        self.assertError(self.validate(), "duplicate ID P-20261020-ab-a01")

    def test_type_must_fit_directory(self):
        path = self.find(ANNA)
        path.rename(self.repo / "places" / path.name)
        self.assertError(self.validate(), "does not belong in places/")

    def test_member_must_be_listed(self):
        self.add("people/P-20261020-zz-a02.md", {"id": "P-20261020-zz-a02", "type": "person", "names": [{"value": "X", "name_type": "birth"}], "vital_status": "deceased"})
        self.assertError(self.validate(), "member 'zz' is not listed")

    def test_invalid_date_in_id(self):
        self.add("people/P-20261340-ab-a02.md", {"id": "P-20261340-ab-a02", "type": "person", "names": [{"value": "X", "name_type": "birth"}], "vital_status": "deceased"})
        self.assertError(self.validate(), "invalid date")

    def test_non_ascii_file_name(self):
        self.find(ANNA).rename(self.repo / "people" / "P-20261020-ab-a01--anna-vzorná.md")
        self.assertError(self.validate(), "must be ASCII")


class Links(FamilyRepoCase):
    def test_broken_link(self):
        self.edit(REC, lambda d: d.update(source="SO-20261020-ab-zzz"))
        self.assertError(self.validate(), "link to SO-20261020-ab-zzz, which does not exist")

    def test_unknown_participant_in_citation(self):
        self.edit("A-20261020-ab-b01", lambda d: d["citations"][0].update(participant="p9"))
        self.assertError(self.validate(), "participant p9 not found")

    def test_duplicate_participant_key(self):
        self.edit(REC, lambda d: d["participants"][3].update(key="p1"))
        self.assertError(self.validate(), "participant key p1 is used twice")

    def test_missing_crop(self):
        self.edit(REC, lambda d: d.update(crop="evidence/missing.jpg"))
        self.assertError(self.validate(), "crop evidence/missing.jpg not found")


class Citations(FamilyRepoCase):
    def test_locator_needs_a_position(self):
        self.edit(REC, lambda d: d.update(locator={"url": "https://example.org/x", "accessed": "2026-10-20"}))
        self.assertError(self.validate(), "locator: needs at least one of page, folio, entry, image")

    def test_url_needs_access_date(self):
        self.edit(REC, lambda d: d["locator"].pop("accessed"))
        self.assertError(self.validate(), "'accessed' is a dependency of 'url'")

    def test_source_needs_collection_or_call_number(self):
        def change(d):
            d.pop("collection")
            d.pop("call_number")
        self.edit(SRC, change)
        self.assertError(self.validate(), "needs collection or call_number")

    def test_record_needs_transcript_section(self):
        path = self.find(REC)
        path.write_text(path.read_text().replace("## Transcript", "## Notes"))
        self.assertError(self.validate(), "'## Transcript' section")


class IdentityGate(FamilyRepoCase):
    def read_once(self, d):
        d["reading"] = {"status": "read-once", "read_by": ["ab"]}

    def test_read_once_cannot_support_proved(self):
        self.edit(REC, self.read_once)
        report = self.validate()
        self.assertError(report, f"{ID_FATHER}.md: identity link relies on {REC}, whose reading is read-once")
        self.assertError(report, f"{REL}.md: proved relationship rests on {REC}")

    def test_read_once_may_support_possible(self):
        self.edit(REC, self.read_once)
        self.edit(ID_FATHER, lambda d: d.update(confidence="possible"))
        self.edit("A-20261020-ab-i02", lambda d: d.update(confidence="possible"))
        self.edit(REL, lambda d: d.update(confidence="possible"))
        self.assertClean(self.validate())

    def test_identity_needs_human_confirmation(self):
        self.edit(ID_FATHER, lambda d: d.pop("confirmed"))
        self.assertError(self.validate(), "identity link needs 'confirmed'")

    def test_proved_relationship_needs_confirmation(self):
        self.edit(REL, lambda d: d.pop("confirmed"))
        self.assertError(self.validate(), "proved relationship needs 'confirmed'")

    def test_proved_relationship_on_weak_assertion(self):
        self.edit("A-20261020-ab-i02", lambda d: d.update(confidence="possible"))
        self.assertError(self.validate(), "rests on A-20261020-ab-i02 with confidence 'possible'")

    def test_confirmed_reading_needs_who_and_when(self):
        self.edit(REC, lambda d: d["reading"].pop("confirmed"))
        self.assertError(self.validate(), "'confirmed' is a required property")

    def test_merge_needs_identity_basis(self):
        # Anna's duplicate file was merged into Anna; basis must be an identity assertion.
        self.edit(ANNA, lambda d: d.update(aliases=[{"id": "P-20261020-ab-a09", "basis": ["A-20261020-ab-b01"], "confirmed": {"by": "ab", "on": "2026-10-20"}}]))
        self.assertError(self.validate(), "basis A-20261020-ab-b01 must be a probable or proved identity assertion")

    def test_alias_resolves_links(self):
        self.edit(ANNA, lambda d: d.update(aliases=[{"id": "P-20261020-ab-a09", "basis": [ID_FATHER], "confirmed": {"by": "ab", "on": "2026-10-20"}}]))
        self.edit("Q-20261020-ab-q01", lambda d: d.update(subjects=["P-20261020-ab-a09"]))
        self.assertClean(self.validate())

    def test_unknown_father_only_for_parent(self):
        self.edit(REL, lambda d: d["parties"][1].update(person="unknown"))
        self.assertError(self.validate(), "only a parent may be 'unknown'")

    def test_parent_child_shape(self):
        self.edit(REL, lambda d: d["parties"].append({"role": "parent", "person": ANNA}))
        self.assertError(self.validate(), "exactly one parent and one child")


class LivingPersons(FamilyRepoCase):
    def add_person(self, pid, status="unknown"):
        self.add(f"people/{pid}.md", {"id": pid, "type": "person", "names": [{"value": "Eva Pokusná", "name_type": "birth"}], "vital_status": status})

    def add_fact(self, aid, pid, fact, date=None, value=None):
        data = {"id": aid, "type": "assertion", "kind": "fact", "subject": pid, "fact_type": fact,
                "citations": [{"source": SRC, "information": "primary", "evidence": "direct"}], "confidence": "probable"}
        if date is not None:
            data["date"] = date
        if value is not None:
            data["value"] = value
        self.add(f"assertions/{aid}.md", data)

    def test_presumed_living_blocks_sensitive_facts(self):
        self.add_person("P-20261020-ab-e01")
        self.add_fact("A-20261020-ab-e02", "P-20261020-ab-e01", "birth", "1950")
        self.add_fact("A-20261020-ab-e03", "P-20261020-ab-e01", "occupation", value="teacher")
        self.assertError(self.validate(), "P-20261020-ab-e01 is (presumed) living")

    def test_old_birth_is_not_living(self):
        self.add_person("P-20261020-ab-e01")
        self.add_fact("A-20261020-ab-e02", "P-20261020-ab-e01", "birth", "1900")
        self.add_fact("A-20261020-ab-e03", "P-20261020-ab-e01", "occupation", value="teacher")
        self.assertClean(self.validate())

    def test_living_minor_without_birth_date(self):
        self.add_person("P-20261020-ab-e01", "living")
        self.add_fact("A-20261020-ab-e02", "P-20261020-ab-e01", "birth", "2015")
        self.assertError(self.validate(), "living minor")

    def test_unknown_status_without_dates_warns(self):
        self.add_person("P-20261020-ab-e01")
        report = self.validate()
        self.assertWarning(report, "cannot tell if the person may be living")
        self.assertWarning(report, "Add a birth or baptism assertion (an estimate is enough")   # ADR 0040: say what to add

    def test_unknown_status_presumed_living_says_what_to_do(self):
        self.add_person("P-20261020-ab-e01")
        self.add_fact("A-20261020-ab-e02", "P-20261020-ab-e01", "birth", "1930")
        report = self.validate()
        self.assertWarning(report, "vital status unknown, born 1930–1930 – treated as living")
        self.assertWarning(report, "set vital_status: deceased; if alive, set vital_status: living")


class Dates(FamilyRepoCase):
    def test_death_before_birth(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1840"))
        self.assertError(self.validate(), "dies before being born")

    def test_approximate_dates_are_widened(self):
        # birth 1850~ (1848–1852), death 1849 is possible under the approximation
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1849"))
        self.assertNotIn("dies before being born", "\n".join(self.validate().errors))

    def test_parent_too_young(self):
        for birth in ("A-20261020-ab-b02", "A-20261020-ab-b05"):  # both versions of Matěj's birth
            self.edit(birth, lambda d: d.update(date="1872"))
        self.assertError(self.validate(), "parent younger than 12")

    def test_father_dead_long_before_birth(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1870"))
        self.assertError(self.validate(), "father died more than a year before")


class Volumes(FamilyRepoCase):
    """A volume of a source in the locator and in coverage ranges (ADR 0058)."""

    COV = "C-20261020-ab-c01"

    def with_volumes(self):
        self.edit(SRC, lambda d: d.update(volumes=[{"volume": "I", "period": "1870/1880"},
                                                   {"volume": "II", "period": "1865/1890", "note": "later entries of older years"}]))

    def test_volume_in_locator_is_valid(self):
        self.edit(REC, lambda d: d["locator"].update(volume="II"))
        self.assertClean(self.validate())

    def test_volume_alone_does_not_locate(self):
        self.edit(REC, lambda d: d.update(locator={"volume": "II"}))
        self.assertError(self.validate(), "locator: needs at least one of page, folio, entry, image")

    def test_volume_must_be_listed_by_the_source(self):
        self.with_volumes()
        self.edit(REC, lambda d: d["locator"].update(volume="III"))
        self.assertError(self.validate(), "locator.volume 'III' is not one of the volumes of SO-20261020-ab-s01 (I, II)")

    def test_volume_matches_without_case(self):
        self.with_volumes()
        self.edit(REC, lambda d: d["locator"].update(volume="ii"))
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("add locator.volume", "\n".join(report.warnings))

    def test_record_without_volume_of_a_source_with_volumes(self):
        self.with_volumes()
        self.assertWarning(self.validate(), "SO-20261020-ab-s01 has volumes (I, II) – add locator.volume")

    def test_volume_listed_twice(self):
        self.edit(SRC, lambda d: d.update(volumes=[{"volume": "II"}, {"volume": "II"}]))
        self.assertError(self.validate(), "volume 'ii' is listed twice in volumes")

    def test_coverage_range_volume(self):
        self.with_volumes()
        self.edit(REC, lambda d: d["locator"].update(volume="I"))
        self.edit(self.COV, lambda d: d["ranges"][0].update(volume="I"))
        self.assertClean(self.validate())
        self.edit(self.COV, lambda d: d["ranges"][0].update(volume="IV"))
        self.assertError(self.validate(), "range volume 'IV' is not one of the volumes of SO-20261020-ab-s01")

    def test_volume_without_a_list_is_free(self):
        self.edit(REC, lambda d: d["locator"].update(volume="Tom. III"))
        self.edit(self.COV, lambda d: d["ranges"][0].update(volume="Tom. III"))
        report = self.validate()
        self.assertClean(report)
        self.assertEqual([w for w in report.warnings if "volume" in w], [])


class Pointers(FamilyRepoCase):
    """ADR 0060: an index points to a book; the pointer is a lead, not a record."""

    INDEX = "C-20261024-ab-i01"
    INDEX_SRC = "SO-20261020-ab-s02"
    BOOK = "C-20261020-ab-c01"     # page-through of SRC, pages 30-60

    def add_index(self, **changes):
        pointer = {"name_as_written": "Pokusný Josef", "event": "baptism", "date_as_written": 1878,
                   "to": {"source": SRC, "page": 41}}
        pointer.update(changes)
        self.add(f"coverage/{self.INDEX}.md", {
            "id": self.INDEX, "type": "coverage", "source": self.INDEX_SRC, "method": "index",
            "ranges": [{"dates": "1870/1890", "query": "letter P"}], "names": ["Pokusný", "Pokusny"],
            "result": "found", "pointers": [pointer], "by": "ab", "on": "2026-10-24"})

    def test_open_pointer_is_valid_and_listed(self):
        self.add_index()
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("no records listed", "\n".join(report.warnings))
        v = RepoValidator(self.repo, ROOT, today=TODAY)
        v.run()
        self.assertEqual([c.id for c, _ in v.open_pointers()], [self.INDEX])

    def test_followed_pointer(self):
        self.add_index(followed=self.BOOK)
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("did not search", "\n".join(report.warnings))
        v = RepoValidator(self.repo, ROOT, today=TODAY)
        v.run()
        self.assertEqual(v.open_pointers(), [])

    def test_book_search_missed_the_page(self):
        self.add_index(to={"source": SRC, "page": 75}, followed=self.BOOK)
        self.assertWarning(self.validate(), "C-20261020-ab-c01 did not search page 75, where the index points for 'Pokusný Josef'")

    def test_book_search_missed_the_volume(self):
        self.edit(SRC, lambda d: d.update(volumes=[{"volume": "I"}, {"volume": "II"}]))
        self.edit(REC, lambda d: d["locator"].update(volume="I"))
        self.edit(self.BOOK, lambda d: d["ranges"][0].update(volume="I"))
        self.add_index(to={"source": SRC, "volume": "II", "page": 41}, followed=self.BOOK)
        self.assertWarning(self.validate(), "C-20261020-ab-c01 did not search volume 'II'")

    def test_pointer_to_an_unknown_volume(self):
        self.edit(SRC, lambda d: d.update(volumes=[{"volume": "I"}]))
        self.add_index(to={"source": SRC, "volume": "IX", "page": 41})
        self.assertError(self.validate(), "pointer to volume 'IX', which is not one of the volumes")

    def test_followed_by_a_search_of_another_book(self):
        self.add_index(followed="C-20261020-ab-c03")
        self.assertError(self.validate(), f"leads to {SRC}, but C-20261020-ab-c03 searched {self.INDEX_SRC}")

    def test_pointer_needs_a_place_in_the_book(self):
        self.add_index(to={"source": SRC})
        self.assertError(self.validate(), "to: needs at least one of page, folio, entry, image")

    def test_pointer_to_the_index_itself(self):
        self.add_index(to={"source": self.INDEX_SRC, "page": 41})
        self.assertError(self.validate(), "leads to the index itself")

    def test_pointers_only_from_an_index(self):
        self.add_index()
        self.edit(self.INDEX, lambda d: d.update(method="page-through", ranges=[{"pages": "1-10"}]))
        self.assertError(self.validate(), "pointers belong to a search of an index (method index), not method 'page-through'")

    def test_pointers_mean_something_was_found(self):
        self.add_index()
        self.edit(self.INDEX, lambda d: d.update(result="negative"))
        self.assertError(self.validate(), "the index gave pointers, so the result is found or partial, not 'negative'")

    def test_index_is_no_evidence_for_a_fact(self):
        self.add_index()
        self.edit("A-20261020-ab-b02", lambda d: d.update(citations=[{"coverage": self.INDEX, "information": "secondary", "evidence": "direct"}]))
        self.assertWarning(self.validate(), f"cites the index search {self.INDEX} as evidence")

    def test_index_for_negative_evidence_is_fine(self):
        self.add_index()
        self.edit("A-20261020-ab-b02", lambda d: d["citations"].append({"coverage": self.INDEX, "evidence": "negative"}))
        self.assertNotIn("cites the index search", "\n".join(self.validate().warnings))

    def test_page_spans(self):
        spans = RepoValidator._page_spans
        self.assertEqual(spans("12-140"), [(12, 140)])
        self.assertEqual(spans("30-60, 70"), [(30, 60), (70, 70)])
        self.assertIsNone(spans("images 5-88"))


class Coverage(FamilyRepoCase):
    def test_negative_needs_names(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(names=[]))
        self.assertError(self.validate(), "names")

    def test_negative_needs_ranges(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(ranges=[]))
        self.assertError(self.validate(), "ranges")

    def test_index_is_no_proof_of_absence(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(method="index"))
        report = self.validate()
        self.assertClean(report)
        self.assertWarning(report, "an index is not proof of absence")

    def test_index_negatives_are_grouped(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(method="index"))
        self.edit("C-20261020-ab-c03", lambda d: d.update(method="index"))
        report = self.validate()
        hits = [w for w in report.warnings if "from an index only" in w]
        self.assertEqual(len(hits), 1, report.warnings)
        self.assertIn("coverage/: 2 negative results from an index only (C-20261020-ab-c02, C-20261020-ab-c03)", hits[0])

    def test_index_negative_can_be_accepted(self):
        accepted = {"by": "ab", "on": "2026-10-20", "note": "the index of this register is complete (checked against 30 pages)"}
        self.edit("C-20261020-ab-c02", lambda d: d.update(method="index", index_negative_accepted=accepted))
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("from an index only", "\n".join(report.warnings))

    def test_acceptance_needs_who_when_why(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(method="index", index_negative_accepted={"by": "ab", "on": "2026-10-20"}))
        self.assertError(self.validate(), "note")

    def test_acceptance_only_for_index_negatives(self):
        self.edit("C-20261020-ab-c02", lambda d: d.update(index_negative_accepted={"by": "ab", "on": "2026-10-20", "note": "x"}))
        self.assertWarning(self.validate(), "index_negative_accepted only fits a negative result from an index")

    def test_found_without_records_warns(self):
        self.edit("C-20261020-ab-c01", lambda d: d.pop("found"))
        self.assertWarning(self.validate(), "no records listed")


class Sessions(FamilyRepoCase):
    def test_session_in_wrong_year(self):
        self.edit("S-20261020-ab-s01", lambda d: d.update(date="2025-12-31"))
        self.assertError(self.validate(), "belongs in sessions/2025/")

    def test_session_needs_next_step(self):
        self.edit("S-20261020-ab-s01", lambda d: d.pop("next_step"))
        self.assertError(self.validate(), "'next_step' is a required property")


if __name__ == "__main__":
    unittest.main()


INQ = "IN-20261020-ab-i01"
SESSION = "S-20261020-ab-s01"
QUESTION = "Q-20261020-ab-q01"
ORAL = "O-20261020-ab-o01"


class Crops(FamilyRepoCase):
    """ADR 0031: several crops; crop stays as the short form."""

    def test_every_crop_must_exist(self):
        self.edit(REC, lambda d: d["crops"].append({"path": "evidence/missing.jpg"}))
        self.assertError(self.validate(), "crop evidence/missing.jpg not found")

    def test_crop_short_form(self):
        self.edit(REC, lambda d: (d.pop("crops"), d.update(crop="evidence/R-20261020-ab-r01-entry.jpg")))
        self.assertClean(self.validate())

    def test_not_both(self):
        self.edit(REC, lambda d: d.update(crop="evidence/R-20261020-ab-r01-entry.jpg"))
        self.assertError(self.validate(), "crop or crops")


class Annotations(FamilyRepoCase):
    """ADR 0032: later notes on a record."""

    def test_annotation_needs_text(self):
        self.edit(REC, lambda d: d["annotations"].append({"hand": "later hand"}))
        self.assertError(self.validate(), "text")

    def test_unknown_field_in_annotation(self):
        self.edit(REC, lambda d: d["annotations"][0].update(colour="red"))
        self.assertError(self.validate(), "colour")

    def test_annotation_date_is_edtf(self):
        self.edit(REC, lambda d: d["annotations"][0].update(event_date="12/11/1902"))
        self.assertError(self.validate(), "event_date")


class Readings(FamilyRepoCase):
    """ADR 0033: readings by the agent and by people; only a person who read it confirms."""

    def test_agent_alone_may_read_once(self):
        self.edit(REC, lambda d: d.update(reading={"status": "read-once", "read_by_agent": True}))
        report = self.validate()
        self.assertNotIn("R-20261020-ab-r01.md: reading", "\n".join(report.errors))

    def test_agent_alone_cannot_confirm(self):
        self.edit(REC, lambda d: d.update(reading={"status": "confirmed", "read_by_agent": "claude-opus-5-5",
                                                   "confirmed": {"by": "ab", "on": "2026-10-20"}}))
        self.assertError(self.validate(), "R-20261020-ab-r01.md", "read_by")

    def test_confirmed_only_by_a_human_reader(self):
        def change(d):
            d["reading"]["read_by"] = ["cd"]
        self.edit(REC, change)
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        self.path("repo.yaml").write_text(text.replace("    role: researcher\n", "    role: researcher\n  - abbr: cd\n    name: Cyril Druhý\n"), encoding="utf-8")
        report = self.validate()
        self.assertError(report, "confirmed by 'ab', who is not among the members who read it")
        self.assertError(report, f"{ID_FATHER}.md: identity link relies on {REC}, whose reading is confirmed by someone who did not read it")

    def test_reading_needs_a_reader(self):
        self.edit(REC, lambda d: d.update(reading={"status": "read-once"}))
        self.assertError(self.validate(), "read_by")


class SecondReading(FamilyRepoCase):
    """ADR 0059: how the second reading was done – after the agent, later, or by another member."""

    def confirm(self, **changes):
        def change(d):
            d["reading"].update({k: v for k, v in changes.items() if k != "confirmed"})
            d["reading"]["confirmed"].update(changes.get("confirmed", {}))
        self.edit(REC, change)

    def add_member(self):
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        self.path("repo.yaml").write_text(text.replace("    role: researcher\n", "    role: researcher\n  - abbr: cd\n    name: Cyril Druhý\n"), encoding="utf-8")

    def test_fixture_after_the_agent_is_clean(self):
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("without basis", "\n".join(report.warnings))

    def test_without_basis_is_a_warning(self):
        def change(d):
            for k in ("basis", "from", "checked"):
                d["reading"]["confirmed"].pop(k)
        self.edit(REC, change)
        report = self.validate()
        self.assertClean(report)
        self.assertWarning(report, "confirmed reading without basis")

    def test_basis_needs_checked_items(self):
        self.edit(REC, lambda d: d["reading"]["confirmed"].pop("checked"))
        self.assertError(self.validate(), "checked")

    def test_after_the_agent_needs_the_agent(self):
        self.edit(REC, lambda d: d["reading"].pop("read_by_agent"))
        self.assertError(self.validate(), "basis member-after-agent needs read_by_agent")

    def test_same_member_later(self):
        self.edit(REC, lambda d: d["reading"].pop("read_by_agent"))
        self.confirm(read_on="2026-10-18", confirmed={"basis": "member-later"})
        self.assertClean(self.validate())

    def test_same_member_the_same_day_is_not_a_second_reading(self):
        self.edit(REC, lambda d: d["reading"].pop("read_by_agent"))
        self.confirm(confirmed={"basis": "member-later"})
        report = self.validate()
        self.assertError(report, "basis member-later needs read_on, the day of the first reading, before confirmed.on")

    def test_same_member_later_needs_the_first_day(self):
        self.edit(REC, lambda d: d["reading"].pop("read_on"))
        self.confirm(confirmed={"basis": "member-later"})
        self.assertError(self.validate(), "basis member-later needs read_on")

    def test_second_member(self):
        self.add_member()
        self.confirm(read_by=["cd", "ab"], confirmed={"basis": "second-member"})
        self.assertClean(self.validate())

    def test_second_member_is_not_the_first_reader(self):
        self.add_member()
        self.confirm(read_by=["ab", "cd"], confirmed={"basis": "second-member"})
        self.assertError(self.validate(), "basis second-member needs two members in read_by")

    def test_second_member_needs_two_readers(self):
        self.confirm(confirmed={"basis": "second-member"})
        self.assertError(self.validate(), "basis second-member needs two members in read_by")

    def test_confirmed_before_the_first_reading(self):
        self.confirm(read_on="2026-10-21")
        self.assertError(self.validate(), "reading confirmed on 2026-10-20, before the first reading on 2026-10-21")

    def test_unknown_basis(self):
        self.confirm(confirmed={"basis": "agent-twice"})
        self.assertError(self.validate(), "basis")


class Speakers(FamilyRepoCase):
    """ADR 0034: several speakers; speaker stays for one."""

    def test_two_speakers_in_the_fixture(self):
        from proavuslib.frontmatter import split
        data, _ = split(self.find(ORAL).read_text(encoding="utf-8"))
        self.assertEqual(data["speakers"], ["P-20261020-ab-l01", "Jan Sousedský (neighbour, fictional)"])

    def test_speaker_short_form(self):
        self.edit(ORAL, lambda d: (d.pop("speakers"), d.update(speaker="Jan Sousedský")))
        self.assertClean(self.validate())

    def test_one_of_speaker_and_speakers(self):
        self.edit(ORAL, lambda d: d.update(speaker="Jan Sousedský"))
        self.assertError(self.validate(), "speaker")
        self.edit(ORAL, lambda d: (d.pop("speaker"), d.pop("speakers")))
        self.assertError(self.validate(), "speaker")

    def test_speaker_person_must_exist(self):
        self.edit(ORAL, lambda d: d["speakers"].append("P-20261020-ab-zzz"))
        self.assertError(self.validate(), "link to P-20261020-ab-zzz, which does not exist")


class QueryRanges(FamilyRepoCase):
    """ADR 0035: database searches as a query instead of dates or pages."""

    def test_query_only_for_database_searches(self):
        self.edit("C-20261020-ab-c03", lambda d: d.update(method="page-through"))
        self.assertError(self.validate(), "a range given only as a query fits a database search")

    def test_query_with_dates_is_fine_for_any_method(self):
        self.edit("C-20261020-ab-c03", lambda d: (d.update(method="page-through"), d["ranges"][0].update(dates="1840/1880")))
        self.assertClean(self.validate())


class Inquiries(FamilyRepoCase):
    """ADR 0036: inquiries to offices as their own entity."""

    def test_answered_needs_date_and_result(self):
        self.edit(INQ, lambda d: d.update(status="answered"))
        self.assertError(self.validate(), "answered", "result")

    def test_dates_in_order(self):
        self.edit(INQ, lambda d: d.update(status="acknowledged", acknowledged="2026-10-01"))
        self.assertError(self.validate(), "acknowledged 2026-10-01 is before sent 2026-10-20")

    def test_not_sent_in_the_future(self):
        self.edit(INQ, lambda d: d.update(sent="2026-11-30"))
        self.assertError(self.validate(), "in the future")

    def test_unknown_status(self):
        self.edit(INQ, lambda d: d.update(status="lost"))
        self.assertError(self.validate(), "status")

    def test_new_id_for_inquiries(self):
        from proavuslib import ids
        self.assertTrue(ids.new_id("inquiry", "ab").startswith("IN-"))
        self.assertEqual(ids.TYPE_BY_PREFIX["IN"], "inquiry")


class HumanTasks(FamilyRepoCase):
    """ADR 0037: human tasks with a state."""

    def test_closed_task_needs_who_and_when(self):
        self.edit(SESSION, lambda d: d["human_tasks"][1].pop("on"))
        self.assertError(self.validate(), "on")

    def test_plain_text_task_still_valid(self):
        self.edit(SESSION, lambda d: d["human_tasks"].append("Call the parish office"))
        self.assertClean(self.validate())

    def test_unknown_state(self):
        self.edit(SESSION, lambda d: d["human_tasks"][0].update(status="waiting"))
        self.assertError(self.validate(), "human_tasks")


class TasksAndQuestions(FamilyRepoCase):
    """ADR 0047: a task names its question; none stays open for a closed one; letters are inquiries."""

    def test_task_links_must_exist(self):
        self.edit(SESSION, lambda d: d["human_tasks"][0].update(question="Q-20261020-ab-q09", conflict="X-20261020-ab-x01",
                                                                 inquiry="IN-20261020-ab-i01"))
        self.assertError(self.validate(), "link to Q-20261020-ab-q09, which does not exist")

    def test_open_task_for_a_closed_question(self):
        for status in ("answered", "bounded", "abandoned"):
            with self.subTest(status=status):
                self.edit(QUESTION, lambda d: d.update(status=status, conclusion="Fictional conclusion."))
                self.assertWarning(self.validate(), f"is for question {QUESTION}, which is {status} – close the task")

    def test_closed_task_for_a_closed_question_is_fine(self):
        self.edit(QUESTION, lambda d: d.update(status="answered", conclusion="Fictional conclusion."))
        self.edit(SESSION, lambda d: d["human_tasks"][0].update(status="dropped", by="ab", on="2026-10-20"))
        self.assertEqual(self.validate().warnings, [])

    def test_letter_or_request_suggests_an_inquiry(self):
        for text in ("Write to farnost-vzorkov@example.org about the burial register",
                     "Počkat na odpověď archivu Vzorkov (fictional)",
                     "Poslat dotaz na matriku Vzorkov (fictional)",
                     "Podat ŽÁDOST o kopii zápisu",
                     "Call the parish office"):     # plain text tasks count too
            with self.subTest(text=text):
                self.edit(SESSION, lambda d: d["human_tasks"].__setitem__(1, text))
                report = self.validate()
                if text.startswith("Call"):
                    self.assertEqual(report.warnings, [])
                else:
                    self.assertWarning(report, "looks like a letter or request to an office – consider an inquiry")

    def test_no_hint_when_linked_to_an_inquiry_or_closed(self):
        self.edit(SESSION, lambda d: d["human_tasks"][0].update(task="Zaplatit poplatek za žádost", inquiry="IN-20261020-ab-i01"))
        self.edit(SESSION, lambda d: d["human_tasks"][1].update(task="Odeslat dotaz e-mailem na podatelna@example.org"))
        self.assertEqual(self.validate().warnings, [])


class RelationshipCitations(FamilyRepoCase):
    """ADR 0038: citations directly on a relationship."""

    def test_participant_of_cited_record_must_exist(self):
        self.edit("RL-20261020-ab-f04", lambda d: d["citations"].append({"record": REC, "participant": "p9"}))
        self.assertError(self.validate(), "participant p9 not found in R-20261020-ab-r01")

    def test_proved_on_citations_needs_confirmed_reading(self):
        def change(d):
            d.update(confidence="proved", confirmed={"by": "ab", "on": "2026-10-20"},
                     citations=[{"record": REC, "participant": "p2", "information": "primary", "evidence": "direct"}])
        self.edit("RL-20261020-ab-f02", change)
        self.assertClean(self.validate())            # citations alone may support a proved relationship
        self.edit(REC, lambda d: d.update(reading={"status": "read-once", "read_by": ["ab"]}))
        self.assertError(self.validate(), "RL-20261020-ab-f02.md: proved relationship cites R-20261020-ab-r01")

    def test_proved_needs_assertions_or_citations(self):
        self.edit("RL-20261020-ab-f02", lambda d: d.update(confidence="proved", confirmed={"by": "ab", "on": "2026-10-20"}))
        self.assertError(self.validate(), "proved relationship needs supporting assertions or citations")


class IdentitySex(FamilyRepoCase):
    """ADR 0040: the participant's sex (stated or from the role) must fit the person."""

    def identity(self, aid, key, person, confidence="possible"):
        self.add(f"assertions/{aid}.md", {"id": aid, "type": "assertion", "kind": "identity",
                                          "participant": {"record": REC, "key": key}, "person": person,
                                          "citations": [{"record": REC, "participant": key}], "confidence": confidence})

    def test_strong_link_with_wrong_sex_is_an_error(self):
        self.edit(MATEJ, lambda d: d.update(sex="female"))
        self.assertError(self.validate(), f"{ID_FATHER}.md: participant p2 of {REC} (role father) does not fit {MATEJ}, who is female")

    def test_stated_sex_wins_over_the_role(self):
        self.identity("A-20261020-ab-s01", "p1", ANNA)                    # p1 is male in the record
        self.assertWarning(self.validate(), f"participant p1 of {REC} (sex male) does not fit {ANNA}, who is female")

    def test_weak_link_only_warns(self):
        self.identity("A-20261020-ab-s02", "p3", JOSEF)                   # p3 is the mother
        report = self.validate()
        self.assertWarning(report, "(role mother) does not fit")
        self.assertNotIn("A-20261020-ab-s02.md: participant", "\n".join(report.errors))

    def test_matching_sex_is_fine(self):
        self.identity("A-20261020-ab-s03", "p3", ANNA)
        self.assertNotIn("does not fit", "\n".join(self.validate().warnings))


class DuplicatePersons(FamilyRepoCase):
    """ADR 0040: same name and overlapping birth – maybe one person in two files."""

    def twin(self, pid="P-20261020-ab-m02", name="Matej Pokusny", birth="1851"):
        self.add(f"people/{pid}.md", {"id": pid, "type": "person", "names": [{"value": name, "name_type": "czech"}],
                                      "sex": "male", "vital_status": "deceased"})
        self.add(f"assertions/A-20261020-ab-t{pid[-2:]}.md", {"id": f"A-20261020-ab-t{pid[-2:]}", "type": "assertion", "kind": "fact",
                 "subject": pid, "fact_type": "birth", "date": birth, "citations": [{"source": SRC}], "confidence": "possible"})

    def test_same_name_and_birth(self):
        self.twin()   # without diacritics – still the same name
        self.assertWarning(self.validate(), f"{MATEJ[:-3]}m01--matej-pokusny.md: may be the same person as P-20261020-ab-m02")

    def test_birth_far_apart_is_no_duplicate(self):
        self.twin(birth="1875")
        self.assertNotIn("may be the same person", "\n".join(self.validate().warnings))

    def test_namesakes_marked_distinct(self):
        self.twin()
        self.edit(MATEJ, lambda d: d.update(distinct_from=["P-20261020-ab-m02"]))
        self.assertNotIn("may be the same person", "\n".join(self.validate().warnings))

    def test_no_birth_no_warning(self):
        self.add("people/P-20261020-ab-m03.md", {"id": "P-20261020-ab-m03", "type": "person",
                 "names": [{"value": "Matěj Pokusný", "name_type": "czech"}], "sex": "male", "vital_status": "deceased"})
        self.assertNotIn("may be the same person", "\n".join(self.validate().warnings))


class DuplicateFacts(FamilyRepoCase):
    """ADR 0040: the same fact twice about one person – join the citations."""

    def test_same_type_and_date(self):
        self.add("assertions/A-20261020-ab-b09.md", {"id": "A-20261020-ab-b09", "type": "assertion", "kind": "fact", "subject": JOSEF,
                 "fact_type": "baptism", "date": "1878-03-14", "citations": [{"source": SRC}], "confidence": "possible"})
        self.assertWarning(self.validate(), f"2 baptism assertions about {JOSEF} with the same date 1878-03-14 (A-20261020-ab-b01, A-20261020-ab-b09)")

    def test_different_values_are_two_facts(self):
        self.add("assertions/A-20261020-ab-o09.md", {"id": "A-20261020-ab-o09", "type": "assertion", "kind": "fact", "subject": MATEJ,
                 "fact_type": "occupation", "value": "weaver", "date": "1878", "citations": [{"source": SRC}], "confidence": "possible"})
        self.assertNotIn("with the same date", "\n".join(self.validate().warnings))


class Roles(FamilyRepoCase):
    """ADR 0044: spouse's parents and grandparents without a side."""

    def test_new_roles_are_known(self):
        def change(d):
            d["participants"].append({"key": "p5", "name_as_written": "Wenceslaus Ukazka", "role": "spouse-father"})
            d["participants"].append({"key": "p6", "name_as_written": "Ludmila", "role": "grandmother", "note": "the groom's"})
        self.edit(REC, change)
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("unknown value", "\n".join(report.warnings))

    def test_role_sex_of_new_roles(self):
        self.edit(REC, lambda d: d["participants"].append({"key": "p5", "name_as_written": "Ludmila", "role": "spouse-mother"}))
        self.add("assertions/A-20261020-ab-r05.md", {"id": "A-20261020-ab-r05", "type": "assertion", "kind": "identity",
                 "participant": {"record": REC, "key": "p5"}, "person": MATEJ,
                 "citations": [{"record": REC, "participant": "p5"}], "confidence": "possible"})
        self.assertWarning(self.validate(), "(role spouse-mother) does not fit P-20261020-ab-m01, who is male")


class PartialDates(FamilyRepoCase):
    """ADR 0045: a date with single unspecified digits is valid."""

    def test_accepted_in_data(self):
        self.edit("A-20261020-ab-b01", lambda d: d.update(date="1878-03-1X"))
        self.assertClean(self.validate())

    def test_date_that_cannot_exist(self):
        self.edit("A-20261020-ab-b01", lambda d: d.update(date="1878-02-3X"))
        self.assertError(self.validate(), "A-20261020-ab-b01.md", "date")


class MaritalStatus(FamilyRepoCase):
    """ADR 0046: marital status in its own fields; old status_as_written stays valid."""

    def test_both_fields_in_one_participant(self):
        self.edit(REC, lambda d: d["participants"][0].update(
            status_as_written="syn nemanželský", marital_status_as_written="svobodný", marital_status="single"))
        report = self.validate()
        self.assertClean(report)
        self.assertEqual(report.warnings, [])

    def test_unknown_normalised_value_only_warns(self):
        self.edit(REC, lambda d: d["participants"][2].update(marital_status_as_written="vdova", marital_status="widow"))
        report = self.validate()
        self.assertClean(report)
        self.assertWarning(report, "unknown value 'widow' in vocabulary marital_statuses")

    def test_old_combined_status_stays_valid(self):
        self.edit(REC, lambda d: d["participants"][0].update(status_as_written="syn nemanželský, svobodný"))
        self.assertClean(self.validate())


class Domicile(FamilyRepoCase):
    """ADR 0051: domicile right with a participant – regional field of cz and at, the same in both."""

    VIENNA_LIKE = "zuständig nach Vzorkov"

    def set_extensions(self, value):
        text = self.path("repo.yaml").read_text(encoding="utf-8").replace("extensions: [cz]", f"extensions: {value}")
        self.path("repo.yaml").write_text(text, encoding="utf-8")

    def add_domicile(self):
        self.edit(REC, lambda d: d["participants"][1].update(
            domicile_as_written=self.VIENNA_LIKE, domicile_place="PL-20261020-ab-v01"))

    def test_with_cz(self):
        self.add_domicile()
        self.assertClean(self.validate())

    def test_with_at_and_both(self):
        self.edit(REC, lambda d: d["participants"][1].pop("house_number"))   # house_number is cz only
        self.edit("A-20261020-ab-d01", lambda d: d.pop("house_number"))
        self.add_domicile()
        for value in ("[at]", "[cz, at]"):
            self.set_extensions(value)
            self.assertClean(self.validate())

    def test_needs_an_extension(self):
        self.add_domicile()
        self.set_extensions("[]")
        self.assertError(self.validate(), "domicile_as_written")

    def test_place_must_exist(self):
        self.edit(REC, lambda d: d["participants"][1].update(domicile_place="PL-20261020-ab-zzz"))
        self.assertError(self.validate(), "domicile_place: link to PL-20261020-ab-zzz")

    def test_church_exit_is_a_known_event_with_at(self):
        self.set_extensions("[cz, at]")
        self.edit(REC, lambda d: d["annotations"].append({"text": "ausgetreten 1925", "event": "church-exit", "event_date": "1925"}))
        report = self.validate()
        self.assertClean(report)
        self.assertEqual(report.warnings, [])

    def test_two_extensions_never_redefine_a_field(self):
        from proavuslib.schemas import SchemaSet
        root = Path(self._tmp.name) / "framework"
        shutil.copytree(ROOT / "schema", root / "schema")
        shutil.copytree(ROOT / "regions", root / "regions")
        ext = root / "regions" / "at" / "schema-ext.yaml"
        ext.write_text(ext.read_text(encoding="utf-8").replace("      type: string\n", "      type: integer\n", 1), encoding="utf-8")
        errors = SchemaSet(root, ["cz", "at"]).extension_errors
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("record#participant.domicile_as_written is already defined differently", errors[0])
        self.assertEqual(SchemaSet(ROOT, ["cz", "at"]).extension_errors, [])


class SearchedBy(FamilyRepoCase):
    """ADR 0052: coverage says whether the member searched or an agent on their instruction."""

    def test_member_and_agent(self):
        self.edit("C-20261020-ab-c01", lambda d: d.update(searched_by="member"))
        self.edit("C-20261020-ab-c02", lambda d: d.update(searched_by="agent", agent_model="claude-opus-5-5"))
        self.assertClean(self.validate())

    def test_agent_model_only_with_agent(self):
        self.edit("C-20261020-ab-c01", lambda d: d.update(searched_by="member", agent_model="claude-opus-5-5"))
        self.assertError(self.validate(), "C-20261020-ab-c01", "agent")
        self.edit("C-20261020-ab-c01", lambda d: d.pop("searched_by"))
        self.assertError(self.validate(), "C-20261020-ab-c01", "searched_by")

    def test_unknown_value(self):
        self.edit("C-20261020-ab-c01", lambda d: d.update(searched_by="robot"))
        self.assertError(self.validate(), "C-20261020-ab-c01", "robot")

    def test_old_coverage_without_it_stays_valid(self):
        self.assertClean(self.validate())
