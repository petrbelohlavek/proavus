#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Evals: does an agent follow the Proavus method? (ADR 0055, evals/README.md)

Framework only – not copied into .proavus/. Every task runs on the fictional
test family; the grade compares the workspace before and after the agent.

Usage:
  eval.py list                          tasks and the rules they test
  eval.py prepare TASK DIR              build the workspace of TASK in an empty DIR
  eval.py grade TASK DIR                grade a workspace after the agent worked in it
  eval.py run TASK|all --agent CMD [--times N] [--label L] [--save] [--keep]
      build a fresh workspace, run CMD in it with the task's prompt on stdin
      (e.g. --agent "claude -p --permission-mode acceptEdits"), grade it;
      N attempts per task (default 3). --save writes the result to
      evals/results/<date>-<label>.json. When the agent itself fails (exit
      code other than 0, timeout), the end of its output is shown and the
      attempt counts as an agent error, not as the model's result.

Exit codes: 0 all checks passed, 1 a check failed, 2 usage error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))

from evalkit import EVALS, Check, Snapshot, Task, all_tasks, load_task, prepare  # noqa: E402

OUTPUT_LINES = 20  # of the agent's output shown when it fails


def grade(task: Task, workspace: Path) -> list[Check]:
    with tempfile.TemporaryDirectory() as tmp:
        before = Snapshot.take(prepare(task, Path(tmp) / "before"))
    return task.grade(before, Snapshot.take(workspace))


def show(checks: list[Check]) -> None:
    for c in checks:
        print(f"  {'PASS' if c.passed else 'FAIL'}  {c.name}" + (f" – {c.detail}" if c.detail and not c.passed else ""))


def run(task: Task, agent: str, timeout: int, keep: bool) -> dict:
    tmp = tempfile.mkdtemp(prefix=f"proavus-eval-{task.id}-")
    workspace = prepare(task, Path(tmp) / "family")
    try:
        done = subprocess.run(agent, shell=True, cwd=workspace, input=task.prompt, text=True,
                              capture_output=True, timeout=timeout)
        status, output = f"exit {done.returncode}", (done.stderr or "") + (done.stdout or "")
        error = done.returncode != 0
    except subprocess.TimeoutExpired as exc:
        status, output, error = "timeout", str(exc.stderr or "") + str(exc.output or ""), True
    checks = grade(task, workspace)
    if keep:
        print(f"  workspace kept: {workspace}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    tail = output.strip().splitlines()[-OUTPUT_LINES:]
    if error:
        # The agent did not finish: its output says why, the checks say nothing about the model.
        print(f"  agent error ({status}):" + "".join(f"\n    {line}" for line in tail or ["(no output)"]))
    return {"agent": status, "error": error, "passed": not error and all(c.passed for c in checks),
            "checks": {c.name: c.passed for c in checks},
            "failed": {c.name: c.detail for c in checks if not c.passed},
            "output": tail if error else []}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Proavus evals: does an agent follow the method?")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("prepare")
    p.add_argument("task")
    p.add_argument("dir", type=Path)
    g = sub.add_parser("grade")
    g.add_argument("task")
    g.add_argument("dir", type=Path)
    r = sub.add_parser("run")
    r.add_argument("task", help="task id or 'all'")
    r.add_argument("--agent", required=True, help="shell command run in the workspace, prompt on stdin")
    r.add_argument("--times", type=int, default=3)
    r.add_argument("--timeout", type=int, default=1800, help="seconds per attempt")
    r.add_argument("--label", default="agent", help="name of the agent and model in the results")
    r.add_argument("--save", action="store_true")
    r.add_argument("--keep", action="store_true", help="keep the workspaces for a look")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        for task in all_tasks():
            print(f"{task.id:24} rules {', '.join(map(str, task.meta.get('rules', [])))} – {task.meta['title']}")
        return 0
    if args.cmd == "prepare":
        prepare(load_task(args.task), args.dir.resolve())
        print(f"prepared {args.dir} – prompt:\n\n{load_task(args.task).prompt}")
        return 0
    if args.cmd == "grade":
        checks = grade(load_task(args.task), args.dir.resolve())
        show(checks)
        return 0 if all(c.passed for c in checks) else 1

    tasks = all_tasks() if args.task == "all" else [load_task(args.task)]
    results = {}
    for task in tasks:
        attempts = []
        for i in range(args.times):
            print(f"{task.id} attempt {i + 1}/{args.times}")
            attempt = run(task, args.agent, args.timeout, args.keep)
            if not attempt["error"]:
                for name, detail in attempt["failed"].items():
                    print(f"  FAIL  {name}" + (f" – {detail}" if detail else ""))
            print(f"  {'agent error' if attempt['error'] else 'passed' if attempt['passed'] else 'failed'} ({attempt['agent']})")
            attempts.append(attempt)
        results[task.id] = {"passed": sum(a["passed"] for a in attempts), "of": len(attempts),
                            "errors": sum(a["error"] for a in attempts), "attempts": attempts}
    print()
    for task_id, res in results.items():
        errors = f" ({res['errors']} agent errors – not counted as the model's result)" if res["errors"] else ""
        print(f"{task_id:24} {res['passed']}/{res['of']}{errors}")
    if args.save:
        out = EVALS / "results" / f"{dt.date.today().isoformat()}-{args.label}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps({"label": args.label, "date": dt.date.today().isoformat(),
                                   "agent": args.agent, "tasks": results}, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"saved {out.relative_to(EVALS.parent)}")
    return 0 if all(r["passed"] == r["of"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
