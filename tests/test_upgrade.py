"""/proavus:upgrade: family_repo.py upgrade-plan / upgrade and migrate.py on the fictional family."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from helpers import FIXTURE, ROOT, TODAY

import build_views
import family_repo
import migrate

NELA = "P-20261020-ab-n01"
TEMPLATE = ROOT / "templates" / "family"
OLD_BLOCK = "<!-- proavus:begin -->\nOld Proavus rules.\n<!-- proavus:end -->"
FAMILY_NOTE = "## Family notes\n\nOur own rule: Grandma's letters stay in the archive box.\n"


class OldRepoCase(unittest.TestCase):
    """A family repository as Proavus 0.1.0 left it: no map, no build_views.py."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "family"
        shutil.copytree(FIXTURE, self.repo)
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        text = text.replace(f"map:\n  root: {NELA}\n", "")
        self.path("repo.yaml").write_text("# family comment, must stay\n" + text, encoding="utf-8")
        for name in ("CLAUDE.md", "AGENTS.md"):
            self.path(name).write_text(f"# {name}\n\n{OLD_BLOCK}\n\n{FAMILY_NOTE}", encoding="utf-8")
        self.path(".github/workflows").mkdir(parents=True)
        self.path(".github/workflows/validate.yml").write_text("name: old\n", encoding="utf-8")
        self.path("README.md").write_text("# Our family\n", encoding="utf-8")
        family_repo.install_tools(self.repo)
        copy = self.path(".proavus")
        (copy / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        (copy / "tools" / "build_views.py").unlink()
        schema = json.loads((copy / "schema" / "repo.schema.json").read_text(encoding="utf-8"))
        schema["properties"]["map"] = {"type": "object", "description": "Settings of the generated family map."}
        (copy / "schema" / "repo.schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
        vocab = copy / "schema" / "vocab" / "fact_types.yaml"
        data = yaml.safe_load(vocab.read_text(encoding="utf-8"))
        data["values"] = [v for v in data["values"] if v["id"] != "other"]
        vocab.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def path(self, rel: str) -> Path:
        return self.repo / rel

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "family_repo.py"), *args, str(self.repo)],
                              capture_output=True, text=True)


class Plan(OldRepoCase):
    def test_plan_from_0_1_0_to_0_2_0(self):
        plan = family_repo.plan_upgrade(self.repo, target="0.2.0")
        self.assertEqual((plan.installed, plan.current, plan.status), ("0.1.0", "0.2.0", "upgrade"))
        heads = [h for h, _ in plan.changelog]
        self.assertEqual(len(heads), 1)
        self.assertTrue(heads[0].startswith("0.2.0"), heads)
        self.assertIn("build_views.py", plan.changelog[0][1])
        self.assertIn("schema/repo.schema.json: + map.lang, + map.root", plan.schema)
        self.assertIn("schema/vocab/fact_types.yaml: + other", plan.schema)
        self.assertFalse(plan.migration)
        self.assertEqual(plan.map_missing, ["root", "lang"])
        self.assertEqual(plan.candidates, [(NELA, "Nela Pokusná")])  # the only person who is nobody's parent

    def test_plan_to_the_plugin_version(self):
        plan = family_repo.plan_upgrade(self.repo)
        self.assertEqual(plan.current, family_repo.framework_version())
        heads = [h.split()[0] for h, _ in plan.changelog]
        self.assertEqual(heads[0], family_repo.framework_version())
        self.assertIn("0.2.0", heads)
        self.assertNotIn("0.1.0", heads)

    def test_cli_plan(self):
        out = self.cli("upgrade-plan")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("0.1.0 · plugin:", out.stdout)
        self.assertIn(f"{NELA}  Nela Pokusná", out.stdout)
        self.assertIn("Migration (migrate.py): not needed", out.stdout)

    def test_newer_copy_is_never_downgraded(self):
        self.path(".proavus/VERSION").write_text("9.0.0\n")
        self.assertEqual(family_repo.plan_upgrade(self.repo).status, "newer")
        self.assertEqual(self.cli("upgrade-plan").returncode, 3)
        with self.assertRaises(SystemExit):
            family_repo.upgrade(self.repo, NELA, "cs")
        self.assertEqual(self.path(".proavus/VERSION").read_text(), "9.0.0\n")

    def test_without_proavus_copy(self):
        shutil.rmtree(self.path(".proavus"))
        plan = family_repo.plan_upgrade(self.repo)
        self.assertEqual((plan.installed, plan.status), (None, "upgrade"))
        family_repo.upgrade(self.repo, NELA)
        self.assertEqual(family_repo.installed_version(self.repo), family_repo.framework_version())

    def test_only_family_repositories(self):
        with self.assertRaises(SystemExit):
            family_repo.plan_upgrade(ROOT)


class Upgrade(OldRepoCase):
    def test_upgrade_0_1_0_with_map_settings(self):
        result = family_repo.upgrade(self.repo, NELA, "cs")
        current = family_repo.framework_version()
        self.assertEqual((result.old, result.new), ("0.1.0", current))
        self.assertEqual(result.report.errors, [])
        self.assertEqual(result.commit_message, f"Upgrade Proavus 0.1.0 → {current}")
        self.assertEqual(family_repo.installed_version(self.repo), current)
        self.assertTrue(self.path(".proavus/tools/build_views.py").is_file())
        self.assertTrue(self.path(".proavus/tools/migrate.py").is_file())
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        self.assertIn(f'schema_version: "{current}"', text)
        self.assertIn(f"map:\n  root: {NELA}\n  lang: cs\n", text)
        self.assertIn("# family comment, must stay", text)
        self.assertEqual(sorted(result.changed), sorted([".proavus/", "CLAUDE.md", "AGENTS.md", ".github/workflows/validate.yml", "repo.yaml"]))

    def test_framework_files_refreshed_family_files_kept(self):
        family_repo.upgrade(self.repo, NELA, "cs")
        for name in ("CLAUDE.md", "AGENTS.md"):
            text = self.path(name).read_text(encoding="utf-8")
            block = family_repo.BLOCK.search((TEMPLATE / name).read_text(encoding="utf-8")).group(0)
            self.assertIn(block, text)
            self.assertNotIn("Old Proavus rules", text)
            self.assertIn(FAMILY_NOTE, text)
        self.assertEqual(self.path(".github/workflows/validate.yml").read_bytes(), (TEMPLATE / ".github/workflows/validate.yml").read_bytes())
        self.assertEqual(self.path("README.md").read_text(), "# Our family\n")

    def test_map_works_after_upgrade(self):
        family_repo.upgrade(self.repo, NELA, "cs")
        out, _ = build_views.build_map(self.repo, today=TODAY)
        page = out.read_text(encoding="utf-8")
        self.assertIn('<html lang="cs">', page)
        self.assertIn("Výchozí osoba", page)

    def test_cli_upgrade_then_current(self):
        out = self.cli("upgrade", "--map-root", NELA, "--map-lang", "en")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn(f"COMMIT: Upgrade Proavus 0.1.0 → {family_repo.framework_version()}", out.stdout)
        self.assertEqual(self.cli("upgrade-plan").returncode, 1)  # already current

    def test_upgrade_without_map_answers(self):
        result = family_repo.upgrade(self.repo)
        self.assertNotIn("map:", self.path("repo.yaml").read_text(encoding="utf-8").replace("# map:", ""))
        self.assertEqual(result.report.errors, [])

    def test_bad_answers_change_nothing(self):
        for root, lang in (("RL-20261020-ab-f01", None), ("Nela", None), (NELA, "de")):
            with self.assertRaises(SystemExit):
                family_repo.upgrade(self.repo, root, lang)
        self.assertEqual(family_repo.installed_version(self.repo), "0.1.0")

    def test_missing_block_is_reported_not_added(self):
        self.path("CLAUDE.md").write_text("# CLAUDE.md\n\nOnly family text.\n", encoding="utf-8")
        result = family_repo.upgrade(self.repo, NELA)
        self.assertEqual(self.path("CLAUDE.md").read_text(encoding="utf-8"), "# CLAUDE.md\n\nOnly family text.\n")
        self.assertTrue(any("CLAUDE.md has no" in w for w in result.warnings))


class MapSettings(unittest.TestCase):
    BASE = "schema_version: 0.1.0\nmembers:\n  - abbr: ab\n    name: A\n"

    def test_add_lang_to_existing_map(self):
        text = family_repo.set_map(self.BASE + f"map:\n  root: {NELA}\n", None, "cs")
        self.assertEqual(yaml.safe_load(text)["map"], {"root": NELA, "lang": "cs"})

    def test_replace_root_keep_rest(self):
        text = family_repo.set_map(self.BASE + "map:\n  lang: en  # labels\n  root: P-20261020-ab-a01\nliving_threshold_years: 110\n", NELA, None)
        data = yaml.safe_load(text)
        self.assertEqual(data["map"], {"lang": "en", "root": NELA})
        self.assertEqual(data["living_threshold_years"], 110)
        self.assertIn("lang: en  # labels", text)

    def test_inline_map_is_left_to_a_human(self):
        with self.assertRaises(SystemExit):
            family_repo.set_map(self.BASE + "map: {lang: en}\n", NELA, None)

    def test_schema_version_line(self):
        text = family_repo.set_schema_version('# c\nschema_version: "0.1.0"\n', "0.3.0")
        self.assertEqual(text, '# c\nschema_version: "0.3.0"\n')


class Migration(OldRepoCase):
    def test_minor_versions_need_no_migration(self):
        self.assertFalse(migrate.needed("0.1.0", "0.9.3"))
        self.assertEqual(migrate.migrate(self.repo, "0.1.0", "0.9.3"), [])

    def test_major_without_migration_is_refused(self):
        plan = family_repo.plan_upgrade(self.repo, target="1.0.0")
        self.assertTrue(plan.migration)
        self.assertEqual(plan.status, "migration-missing")
        self.assertIn("0→1", plan.message)
        with mock.patch.object(family_repo, "framework_version", return_value="1.0.0"):
            with self.assertRaises(SystemExit):
                family_repo.upgrade(self.repo)
        self.assertEqual(family_repo.installed_version(self.repo), "0.1.0")

    def test_major_upgrade_runs_the_migration(self):
        def zero_to_one(repo: Path) -> list[str]:
            (repo / "assertions" / "MIGRATED").write_text("v1\n")
            return ["assertions/MIGRATED"]

        with mock.patch.dict(migrate.MIGRATIONS, {0: zero_to_one}), \
                mock.patch.object(family_repo, "framework_version", return_value="1.0.0"):
            plan = family_repo.plan_upgrade(self.repo)
            self.assertEqual((plan.status, plan.migration), ("upgrade", True))
            result = family_repo.upgrade(self.repo, NELA)
        self.assertIn("assertions/MIGRATED", result.changed)
        self.assertEqual(self.path("assertions/MIGRATED").read_text(), "v1\n")
        self.assertIn('schema_version: "1.0.0"', self.path("repo.yaml").read_text(encoding="utf-8"))

    def test_cli(self):
        tool = str(ROOT / "tools" / "migrate.py")
        same = subprocess.run([sys.executable, tool, str(self.repo), "--from", "0.1.0", "--to", "0.3.0"], capture_output=True, text=True)
        self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
        self.assertIn("nothing to migrate", same.stdout)
        major = subprocess.run([sys.executable, tool, str(self.repo), "--from", "0.3.0", "--to", "1.0.0"], capture_output=True, text=True)
        self.assertEqual(major.returncode, 3)
        self.assertIn("does not have", major.stdout)


if __name__ == "__main__":
    unittest.main()
