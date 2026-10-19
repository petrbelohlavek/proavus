"""validate.py on the fictional family repository: one test per rule."""

from __future__ import annotations

import subprocess
import sys
import unittest

from helpers import FamilyRepoCase, ROOT

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
        self.assertEqual(report.files, 16)

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
        self.assertError(report, f"{ID_FATHER}.md: identity link relies on {REC}, which is read-once read")
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
        self.assertWarning(self.validate(), "cannot tell if the person may be living")


class Dates(FamilyRepoCase):
    def test_death_before_birth(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1840"))
        self.assertError(self.validate(), "dies before being born")

    def test_approximate_dates_are_widened(self):
        # birth 1850~ (1848–1852), death 1849 is possible under the approximation
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1849"))
        self.assertNotIn("dies before being born", "\n".join(self.validate().errors))

    def test_parent_too_young(self):
        self.edit("A-20261020-ab-b02", lambda d: d.update(date="1872"))
        self.assertError(self.validate(), "parent younger than 12")

    def test_father_dead_long_before_birth(self):
        self.edit("A-20261020-ab-d01", lambda d: d.update(date="1870"))
        self.assertError(self.validate(), "father died more than a year before")


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
