#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Block family data from entering the framework repository.

Scans files (and their paths) for names from a guard list kept OUTSIDE the
repository (default: ../.guard-names next to the repo, or the path in the
environment variable PROAVUS_GUARD_NAMES). Matching ignores case and
diacritics and works on whole words. Phrases listed in .guard-allow (repo
root) are removed before matching, so the author's attribution may stay.

The guard list itself is never printed: a hit reports the file, line and the
entry number in the list only.

Usage:
  guard_names.py --staged          check what is staged for commit (pre-commit hook)
  guard_names.py --message FILE    check a commit message (commit-msg hook)
  guard_names.py --all             check all tracked and untracked, non-ignored files
  guard_names.py PATH ...          check given files

Exit codes: 0 clean, 1 hit found, 2 guard list missing or unreadable.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def split_camel(text: str) -> str:
    """matejPokusny → matej Pokusny, so names inside identifiers are found."""
    out = []
    for i, c in enumerate(text):
        if i and c.isupper() and text[i - 1].islower():
            out.append(" ")
        out.append(c)
    return "".join(out)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def read_list(path: Path) -> list[str]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line)
    return entries


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if out.returncode == 0:
        return Path(out.stdout.strip())
    return Path.cwd()


def guard_list_path(root: Path) -> Path:
    env = os.environ.get("PROAVUS_GUARD_NAMES")
    return Path(env) if env else root.parent / ".guard-names"


class Guard:
    def __init__(self, names: list[str], allowed: list[str]):
        self.patterns = [
            # A name is a whole word between non-letters: underscores and
            # digits separate words too (novak_line, novak2 are hits).
            (i + 1, re.compile(r"(?<![^\W\d_])" + re.escape(normalize(n)) + r"(?![^\W\d_])"))
            for i, n in enumerate(names)
        ]
        # Longest first, so a longer allowed phrase wins over its prefix.
        self.allowed = sorted({normalize(a) for a in allowed}, key=len, reverse=True)

    def hits(self, text: str) -> list[tuple[int, int]]:
        """Return (line number, guard entry number) pairs."""
        found = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            norm = normalize(split_camel(line))
            for phrase in self.allowed:
                norm = norm.replace(phrase, " ")
            for entry, pattern in self.patterns:
                if pattern.search(norm):
                    found.append((lineno, entry))
        return found


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        capture_output=True, text=True, check=True,
    )
    return [p for p in out.stdout.split("\0") if p]


def all_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True, text=True, check=True,
    )
    return [p for p in out.stdout.split("\0") if p]


def staged_content(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f":{path}"], capture_output=True, check=True
    ).stdout


def as_text(data: bytes) -> str | None:
    if b"\0" in data[:8192]:
        return None  # binary
    return data.decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--message", metavar="FILE")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)

    root = repo_root()
    list_path = guard_list_path(root)
    try:
        names = read_list(list_path)
    except OSError:
        print(
            f"guard: guard list not found at {list_path} "
            "(set PROAVUS_GUARD_NAMES). Commit blocked.",
            file=sys.stderr,
        )
        return 2
    allow_path = root / ".guard-allow"
    allowed = read_list(allow_path) if allow_path.exists() else []
    guard = Guard(names, allowed)

    problems: list[str] = []

    def check(label: str, text: str | None) -> None:
        for lineno, entry in guard.hits(label):
            problems.append(f"{label}: file path matches guard entry #{entry}")
        if text is None:
            return
        for lineno, entry in guard.hits(text):
            problems.append(f"{label}:{lineno}: matches guard entry #{entry}")

    if args.message:
        check("commit message", Path(args.message).read_text(encoding="utf-8"))
        # The label itself is not a path; drop false path hits.
        problems = [p for p in problems if "file path" not in p]
    elif args.staged:
        for path in staged_files():
            check(path, as_text(staged_content(path)))
    else:
        paths = all_files() if args.all else args.paths
        for path in paths:
            full = root / path if not Path(path).is_absolute() else Path(path)
            if full.is_file():
                check(path, as_text(full.read_bytes()))

    if problems:
        print("guard: possible family data found – not allowed in the framework:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        print("Replace with fictional examples (see AGENTS.md).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
