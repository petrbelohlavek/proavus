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

## 3. Confirm the plan

Show: folder, repository name, owner (`gh api user --jq .login`), visibility
**private**, member, regions. Continue only after a clear yes.

## 4. Create the files

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" init "<folder>/proavus-<family>" --title "<title>" --member <abbr>:"<Full name>" --region cz
```

The tool refuses a non-empty folder – then ask for another one.

## 5. Save locally

In the new folder: `git init -b main`, `git add -A`,
`git commit -m "Create family repository (Proavus <version>)"`
(version from `.proavus/VERSION`).

## 6. Create the private repository on GitHub

After the user's yes:

```
gh repo create <owner>/proavus-<family> --private --source "<folder>/proavus-<family>" --remote origin --push
```

## 7. Verify it is private

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private "<folder>/proavus-<family>"
```

Exit 0 = private. Anything else: stop, tell the user plainly, and help make
the repository private (`gh repo edit <owner>/proavus-<family> --visibility
private --accept-visibility-change-consequences`) before any data is added.

## 8. Hand over

Tell the user: open the new folder in a new Claude Code session and type
`/start`. To invite family members later: GitHub → repository → Settings →
Collaborators (only trusted people; members who leave keep what they
downloaded). Recommend two-factor login on GitHub for everyone.
