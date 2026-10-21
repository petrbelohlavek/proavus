---
name: init
description: Create a new private Proavus family repository from the template (run as /proavus:init). Use when someone wants to start their own family tree with Proavus.
argument-hint: "[family name]"
disable-model-invocation: true
---

# Create a private family repository

Goal: a new **private** repository `proavus-<family>` with the Proavus
template and a pinned copy of the tools in `.proavus/`. Answer in the user's
language; explain each step in one plain sentence and ask before every step
that creates something or touches GitHub.

**Never** create a public repository, never use a fork of `proavus` for family
data (forks are public), never put family data into the `proavus` framework.

## 1. Check the computer

Run `git --version`, `gh auth status` and `uv --version`. If something is
missing or `gh` is not logged in, tell the user what is missing and how to
install it (macOS: `brew install git gh uv`; Windows: `winget install
Git.Git GitHub.cli astral-sh.uv`; then `gh auth login` in the browser and
`gh auth setup-git`). Stop until it works. Never ask for passwords or tokens.

## 2. Ask (one short message)

- family name for the repository name → `proavus-<family>` (lowercase ASCII,
  e.g. `proavus-novak`; default `proavus-family`). $ARGUMENTS may already
  contain it;
- title of the tree (any language, e.g. "Rodokmen rodiny Novákových");
- the user's full name and a 2–4 letter lowercase abbreviation (used in IDs);
- regions researched (offer `cz`; others have no regional package yet);
- parent folder (suggest `~/Documents/Proavus/`). It must not be inside
  iCloud Drive, Dropbox, OneDrive or Google Drive (they damage `.git`) and
  must not be inside the `proavus` framework folder.

**Existing empty repository.** If the user already created the repository on
GitHub (or the current folder is its empty clone), use it: the folder must
contain only `.git` (and possibly `.claude/`, which Claude Code creates when
the folder is opened) and have a remote `origin`. Check it **before writing any
file**:

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private "<folder>"
```

Exit 0 = private, continue. Exit 3 = public or a fork: stop and help make it
private first. Exit 4 = cannot tell: fix `gh` first. If the folder has
commits or files other than `.git` and `.claude/`, stop – never overwrite an
existing repository.

## 3. Confirm the plan

Show: folder, repository name, owner (`gh api user --jq .login`), visibility
**private**, new or existing repository, member, regions. Continue only after
a clear yes.

## 4. Create the files

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" init "<folder>" --title "<title>" --member <abbr>:"<Full name>" --region cz
```

The tool refuses a folder with anything but `.git` and `.claude/` in it –
then ask for another one.

## 5. Protect the framework

The family repository must never change the Proavus framework (family data
would leak into it). Tell the user in one sentence, then run:

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" protect-plugin "<folder>"
```

It adds `Edit(//<plugin folder>/**)` to `permissions.deny` in
`<folder>/.claude/settings.local.json` (keeps everything else there; the file
is per computer and not saved in git). One `Edit` rule blocks all of Claude
Code's file-editing tools (Edit, Write …); a `Write(path)` rule would not
work. If the plugin was installed from GitHub and the user also keeps a local
checkout of the framework, protect it too: `--also "<checkout>"`.

Say plainly what this does **not** do: a shell command (`sed -i`, `>`, a
script) can still write anywhere – the rule does not cover the shell. That
the framework stays untouched from a Bash command relies on the agent
following `AGENTS.md`, and on the person approving commands, not on this
setting.

## 6. Save locally

In the folder: if there is no `.git` yet, `git init -b main`; otherwise
`git branch -M main` (an empty clone may start on another branch name). Then
`git add -A` and switch on the check before every commit (one sentence for
the user: from now on git refuses to save data with errors):

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" hooks "<folder>"
uv run .proavus/tools/validate.py .
```

(it sets `core.hooksPath` to `.githooks` – per computer, not saved in git –
and marks the hook executable in git for the other members' clones). With 0
errors: `git commit -m "Create family repository (Proavus <version>)"`
(version from `.proavus/VERSION`). If the commit is stopped with "Commit
zastaven / Commit stopped", the pre-commit hook found validation errors in
what is being saved: explain them plainly, fix them with the user and commit
again. Never bypass the hook
(`--no-verify`, changing `core.hooksPath`).

## 7. Put it on GitHub (private)

After the user's yes:

- **new repository:**
  `gh repo create <owner>/proavus-<family> --private --source "<folder>" --remote origin --push`
- **existing empty repository** (already checked in step 2):
  `git push -u origin main`

## 8. Verify it is private

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private "<folder>"
```

Exit 0 = private. Anything else: stop, tell the user plainly, and help make
the repository private (`gh repo edit <owner>/proavus-<family> --visibility
private --accept-visibility-change-consequences`) before any data is added.

## 9. Hand over

Tell the user: open the new folder in a new Claude Code session and type
`/proavus:start`; end every session with `/proavus:end`. To invite family members later: GitHub → repository → Settings →
Collaborators (only trusted people; members who leave keep what they
downloaded). Recommend two-factor login on GitHub for everyone.
