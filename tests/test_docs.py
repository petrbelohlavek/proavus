"""README (for everyone, EN and CS), TECHNICAL.md and the public project files: links work,
the picture is current (ADR 0053), issue forms ask for no family data (ADR 0054)."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from helpers import ROOT

PAGES = ["README.md", "README.cs.md", "TECHNICAL.md"]
COMMUNITY = ["CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"]
LINK = re.compile(r'(?:\]\(|src="|srcset="|href=")([^)"#\s]+)(?:#[^)"]*)?[)"]')


class Pages(unittest.TestCase):
    def test_local_links_exist(self):
        for page in PAGES + COMMUNITY:
            for target in LINK.findall((ROOT / page).read_text(encoding="utf-8")):
                if "://" in target or target.startswith("mailto:"):
                    continue
                self.assertTrue((ROOT / target).exists(), f"{page}: {target}")

    def test_switches(self):
        """Language and audience switch on every page; the README for everyone stays plain."""
        for page in PAGES:
            text = (ROOT / page).read_text(encoding="utf-8")
            self.assertIn('href="TECHNICAL.md"' if page != "TECHNICAL.md" else 'href="README.md"', text, page)
        for page in ("README.md", "README.cs.md"):
            text = (ROOT / page).read_text(encoding="utf-8")
            for word in ("marketplace", "git clone", "uv run", "commit", "schema"):
                self.assertNotIn(word, text, f"{page} is for everyone – {word!r} belongs in TECHNICAL.md")

    def test_picture_is_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "architecture.py"
            script.write_text((ROOT / "docs/images/architecture.py").read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run([sys.executable, str(script)], check=True)
            for name in ("proavus-architecture.svg", "proavus-architecture-dark.svg"):
                self.assertEqual((Path(tmp) / name).read_text(encoding="utf-8"),
                                 (ROOT / "docs/images" / name).read_text(encoding="utf-8"),
                                 f"{name} is out of date – run python3 docs/images/architecture.py")


class IssueForms(unittest.TestCase):
    FORMS = ROOT / ".github" / "ISSUE_TEMPLATE"

    def test_only_forms(self):
        config = yaml.safe_load((self.FORMS / "config.yml").read_text(encoding="utf-8"))
        self.assertIs(config["blank_issues_enabled"], False)
        self.assertTrue(any("security/advisories/new" in link["url"] for link in config["contact_links"]))

    def test_every_form_asks_for_no_family_data(self):
        forms = sorted(self.FORMS.glob("*.yml"))
        forms = [f for f in forms if f.name != "config.yml"]
        self.assertTrue(forms)
        for form in forms:
            body = yaml.safe_load(form.read_text(encoding="utf-8"))["body"]
            required = [option for item in body if item["type"] == "checkboxes"
                        for option in item["attributes"]["options"] if option.get("required")]
            self.assertTrue(any("no real family data" in option["label"] for option in required), form.name)


if __name__ == "__main__":
    unittest.main()
