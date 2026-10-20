"""GitHub workflows of the framework and the family template: pinned actions, minimal permissions (ADR 0043)."""

from __future__ import annotations

import re
import unittest

import yaml

from helpers import ROOT

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml")) + sorted(
    (ROOT / "templates" / "family" / ".github" / "workflows").glob("*.yml"))
PINNED = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")


def uses(path):
    """(action@ref, version comment) of every step that uses an action."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-?\s*uses:\s*(\S+)\s*(?:#\s*(\S+))?", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


class Workflows(unittest.TestCase):
    def test_there_are_workflows(self):
        self.assertEqual({p.name for p in WORKFLOWS}, {"ci.yml", "validate.yml"})

    def test_actions_pinned_to_a_commit(self):
        for path in WORKFLOWS:
            for action, version in uses(path):
                self.assertRegex(action, PINNED, f"{path.name}: {action} is not pinned to a full commit SHA")
                self.assertRegex(version or "", r"^v[0-9]+\.[0-9]+\.[0-9]+$", f"{path.name}: {action} needs a # vX.Y.Z comment")

    def test_framework_and_template_use_the_same_pins(self):
        pins = [dict(a.split("@") for a, _ in uses(p)) for p in WORKFLOWS]
        self.assertEqual(pins[0], pins[1])

    def test_minimal_permissions(self):
        for path in WORKFLOWS:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(data["permissions"], {}, f"{path.name}: no permissions at the workflow level")
            for name, job in data["jobs"].items():
                self.assertEqual(job.get("permissions"), {"contents": "read"}, f"{path.name}: job {name} may only read")

    def test_checkout_keeps_no_token(self):
        for path in WORKFLOWS:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            for job in data["jobs"].values():
                for step in job["steps"]:
                    if step.get("uses", "").startswith("actions/checkout@"):
                        self.assertIs(step.get("with", {}).get("persist-credentials"), False, path.name)

    def test_dependabot_watches_actions(self):
        data = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        ecosystems = {u["package-ecosystem"]: u for u in data["updates"]}
        self.assertIn("github-actions", ecosystems)
        self.assertEqual(ecosystems["github-actions"]["directory"], "/")


if __name__ == "__main__":
    unittest.main()
