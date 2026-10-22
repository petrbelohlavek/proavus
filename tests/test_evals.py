"""Evals (ADR 0055): every task builds a valid workspace, and its graders
pass the reference solution and catch the wrong ones."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "evals"))

import eval as eval_tool  # noqa: E402
from evalkit import Snapshot, all_tasks, overlay, prepare  # noqa: E402


class Tasks(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def grade(self, task, reference: Path | None):
        here = Path(tempfile.mkdtemp(dir=self.tmp))
        before = Snapshot.take(prepare(task, here / "before"))
        workspace = prepare(task, here / "after")
        if reference:
            overlay(reference, workspace)
        return {c.name: c for c in task.grade(before, Snapshot.take(workspace))}

    def test_there_are_tasks(self):
        self.assertGreaterEqual(len(all_tasks()), 3)

    def test_task_files(self):
        for task in all_tasks():
            for key in ("title", "rules", "prompt", "expect"):
                self.assertIn(key, task.meta, task.id)
            self.assertTrue((task.dir / "reference" / "pass").is_dir(), task.id)
            self.assertTrue(list((task.dir / "reference").glob("fail-*")), f"{task.id}: no wrong solution")

    def test_workspace_is_valid(self):
        for task in all_tasks():
            snap = Snapshot.take(prepare(task, self.tmp / task.id))
            self.assertEqual(snap.errors, [], task.id)
            self.assertTrue((snap.root / ".proavus" / "tools" / "validate.py").is_file())

    def test_doing_nothing_fails(self):
        for task in all_tasks():
            checks = self.grade(task, None)
            self.assertFalse(all(c.passed for c in checks.values()), task.id)

    def test_reference_solutions(self):
        for task in all_tasks():
            for ref in sorted((task.dir / "reference").iterdir()):
                checks = self.grade(task, ref)
                failed = {n for n, c in checks.items() if not c.passed}
                if ref.name == "pass":
                    self.assertEqual(failed, set(), f"{task.id}/pass: {[checks[n].detail for n in failed]}")
                else:
                    expected = set((ref / "_expect.txt").read_text(encoding="utf-8").split())
                    self.assertTrue(expected, f"{task.id}/{ref.name}: _expect.txt names the checks it must fail")
                    self.assertLessEqual(expected, set(checks), f"{task.id}/{ref.name}: unknown check")
                    self.assertLessEqual(expected, failed, f"{task.id}/{ref.name}")


class Cli(unittest.TestCase):
    def test_list_and_grade(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(eval_tool.main(["list"]), 0)
        self.assertIn("namesakes", out.getvalue())
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            workspace = Path(tmp) / "family"
            eval_tool.main(["prepare", "namesakes", str(workspace)])
            self.assertEqual(eval_tool.main(["grade", "namesakes", str(workspace)]), 1)

    def test_run_with_a_fake_agent(self):
        """The runner gives the prompt on stdin in the workspace; an agent that does nothing fails."""
        out = io.StringIO()
        with redirect_stdout(out):
            code = eval_tool.main(["run", "namesakes", "--agent", f'"{sys.executable}" -c "import sys; sys.stdin.read()"',
                                   "--times", "1"])
        self.assertEqual(code, 1)
        self.assertIn("namesakes", out.getvalue())
        self.assertIn("0/1", out.getvalue())

    def test_agent_error_is_shown(self):
        """An agent that fails shows why; the attempt is an agent error, not the model's result."""
        out = io.StringIO()
        fail = f'"{sys.executable}" -c "import sys; sys.stdin.read(); sys.exit(\'Error: not logged in\')"'
        with redirect_stdout(out):
            code = eval_tool.main(["run", "namesakes", "--agent", fail, "--times", "1"])
        self.assertEqual(code, 1)
        self.assertIn("agent error (exit 1)", out.getvalue())
        self.assertIn("Error: not logged in", out.getvalue())
        self.assertIn("1 agent errors", out.getvalue())
        self.assertNotIn("FAIL  both-entries-recorded", out.getvalue())


if __name__ == "__main__":
    unittest.main()
