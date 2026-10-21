---
name: setup
description: Set up Proavus on a family member's computer (run as /proavus:setup) – check and install git, gh and uv, log in to GitHub in the browser, install the plugin from the catalogue, clone the private family repository, add the member to repo.yaml and start the first session. Use when a family member without technical knowledge joins an existing family repository.
argument-hint: "[owner/proavus-family]"
disable-model-invocation: true
---

# Set up Proavus for a family member

The person in front of you has no technical knowledge. Answer in their
language, one step at a time: say in one plain sentence what the step does
and why, ask before every step that installs, logs in, downloads or saves
something, and wait for their answer. Never show a wall of commands; run them
yourself and tell the result in words.

Every step first **checks** whether it is already done and then skips it, so
the guide can be run again after a restart, a new session or an error.

**Never in the chat:** passwords, tokens, recovery codes or keys. Never ask
for them, never run `gh auth token`, `gh auth status --show-token` or
anything that prints a token, never put a token into a command, a file or
the git remote. If the user starts typing a password or a token into the
chat, stop them and say it belongs only into GitHub's own page in the browser
or a system window of their computer. If one was pasted anyway, tell them to
change that password (or delete that token on github.com → Settings) and do
not repeat it.

Never write family data into the `proavus` framework, never into a public
repository or a fork of `proavus`.

## 0. Where am I running from

- `/proavus:setup` (the plugin is installed): the framework is
  `${CLAUDE_PLUGIN_ROOT}`; step 4 only checks the version.
- Following this file by hand (first run on a new computer, the plugin is
  not installed yet): the framework is the folder this file lies in, two
  levels up (`<framework>/skills/setup/SKILL.md`). Use that folder wherever
  this guide says `${CLAUDE_PLUGIN_ROOT}`.

Find out the system: macOS or Windows (`uname -s` gives `Darwin` on macOS
and `MINGW…`/`MSYS…` in Git Bash on Windows, which Claude Code uses there –
so git is usually present on Windows already). Linux: the same steps with the
system's package manager.

## 1. Ask (one short message)

- the family repository, e.g. `novakovi/proavus-novak` (the maintainer sends
  it; $ARGUMENTS may already contain it);
- their full name and a 2–4 letter lowercase abbreviation for the IDs (offer
  one from the initials, e.g. Jana Nováková → `jn`);
- their role in the research – in plain words:
  - **researcher** (`researcher`) – searches and reads records (the usual
    choice),
  - **helper** (`helper`) – helps now and then: memories, photos, a visit to
    an archive,
  - **maintainer** (`maintainer`) – looks after the repository and invites
    others (only if the family agreed);
- the parent folder (suggest `~/Documents/Proavus/`; on Windows
  `Documents\Proavus`). Not inside iCloud Drive, Dropbox, OneDrive or Google
  Drive (they damage `.git`), not inside the `proavus` framework folder.

## 2. Programs: git, gh, uv

Check: `git --version`, `gh --version`, `uv --version`. For each one that is
missing, say what it is for (git – keeps the history of the research; gh –
talks to GitHub; uv – runs the Proavus tools, it downloads Python itself) and
install it after a yes.

**macOS**

- Homebrew present (`brew --version`): `brew install git gh uv`.
- Without Homebrew (do not install Homebrew for them – it needs the Mac
  password in a terminal):
  - git: `xcode-select --install` – a system window opens; the user clicks
    *Install* and waits (several minutes). Check with `git --version`.
  - uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (installs into the
    user's own folder, no password).
  - gh: the user downloads the macOS installer (`.pkg`) from
    https://github.com/cli/cli/releases/latest and opens it. If the Mac asks
    for their password, they type it **into that system window** – never into
    the chat.

**Windows** (PowerShell or the session's shell):

```
winget install --id Git.Git -e --source winget
winget install --id GitHub.cli -e --source winget
winget install --id astral-sh.uv -e --source winget
```

If Windows asks for permission, the user confirms it in the system window.
`winget` missing: install *App Installer* from the Microsoft Store.

After installing: a new program is often not found until the shell starts
again. Check again; if it is still missing, ask the user to restart the
Claude app (or start a new session) and run `/proavus:setup` again – done
steps are skipped.

## 3. GitHub account and login

The user needs their own GitHub account (github.com → Sign up; they create it
themselves in the browser). Check `gh auth status`:

- logged in: say as which account (`gh api user --jq .login`) and ask
  whether that is them;
- not logged in: run in the background
  `gh auth login --web --hostname github.com --git-protocol https`.
  It prints a one-time code (e.g. `ABCD-1234`) and opens github.com in the
  browser. Tell the user the code and to type it on that page, then confirm
  the access there with their own GitHub password (in the browser only). The
  one-time code is not a password: it works only together with their login
  in the browser and expires in minutes. If the browser does not open, the
  address is https://github.com/login/device. If the command waits for
  *Enter* or fails without a terminal, ask the user to open Terminal
  (macOS) or PowerShell (Windows), type the same command themselves and
  follow it.
- then `gh auth setup-git` (git uses the gh login – no password for git) and
  `gh auth status` again.

**Two-factor login (2FA).** Recommend it strongly: the repository holds
data of living relatives. On github.com → Settings → Password and
authentication → *Enable two-factor authentication*, with an authenticator
app or a passkey; the recovery codes are saved outside the computer (printed
or in a password manager) – never in the chat, never in the repository.
GitHub requires 2FA for most accounts anyway. The user does it in the
browser; you only explain.

## 4. The Proavus plugin

Check: the commands `/proavus:start`, `/proavus:end` exist in this session
(you were started as `/proavus:setup`), or `claude plugin list` lists
`proavus@proavus`. If yes, compare its version
(`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`) with the family
repository's `.proavus/VERSION` after step 5; an older plugin is updated as
in Proavus TECHNICAL.md, "Update to a new release".

Not installed: the framework repository is its own plugin catalogue (ADR
0014). Until Proavus is public, the user's GitHub account needs access to
`petrbelohlavek/proavus` (the maintainer arranges it; `gh repo view
petrbelohlavek/proavus` must work).

1. Get the framework on the `stable` branch (the last release), outside the
   family folder:
   `git clone --branch stable https://github.com/petrbelohlavek/proavus.git <parent>/proavus`
   (already there: `git -C <parent>/proavus switch stable` and `git pull`).
2. Add the catalogue and install – if the `claude` command is available:
   ```
   claude plugin marketplace add <parent>/proavus
   claude plugin install proavus@proavus
   ```
   Without it (desktop app only): the user types in the message box
   `/plugin marketplace add <parent>/proavus` and then
   `/plugin install proavus@proavus`.
3. Sessions started before the installation do not see the plugin: the user
   restarts the Claude app (or opens a new session) and types
   `/proavus:setup` – the steps done so far are skipped.

## 5. The family repository

Before downloading anything:

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" access <owner/proavus-family>
```

- **7** – not found or no access yet: the maintainer must invite the user
  (GitHub → repository → Settings → Collaborators). The invitation comes by
  e-mail and on github.com → notifications; the user accepts it in the
  browser (`gh api user/repository_invitations --jq '.[].repository.full_name'`
  lists open invitations). Then run `access` again.
- **3** – public or a fork: **stop**. Do not download or write anything;
  tell the user to contact the maintainer – family data must be in a private
  repository.
- **4** – cannot tell: fix the login (step 3) first.
- **0, 2, 6** – private: continue; remember the code for step 6.

Clone (after a yes), unless the folder is already a clone of this repository
(`git -C <folder> remote get-url origin`):

```
gh repo clone <owner/proavus-family> "<parent>/proavus-<family>"
```

Then check the clone: `repo.yaml` and `.proavus/` must be there (otherwise it
is not a Proavus family repository – stop and ask the maintainer), and

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private "<folder>"
```

must give exit 0. Protect the framework from edits made in the family
repository (one sentence of explanation, as in `/proavus:init` step 5):

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" protect-plugin "<folder>"
```

(with `--also "<parent>/proavus"` if the framework was cloned in step 4).

Switch on the check before every commit – `core.hooksPath` is set per
computer, so every clone needs it (one sentence: git then refuses to save
data with errors):

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" hooks "<folder>"
```

If it says `.githooks/pre-commit` is missing, the family repository is older
than Proavus 0.5.0: continue, and tell the user that the maintainer (or they
themselves in the first session) should run `/proavus:upgrade`.

## 6. Add the member to repo.yaml

Look at `members` in `<folder>/repo.yaml`. Already listed (the same name)?
Skip. Show the new line (abbreviation, name, role) and after a yes:

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" add-member "<folder>" --abbr <abbr> --name "<Full name>" --role <role>
uv run "<folder>/.proavus/tools/validate.py" "<folder>"
```

The tool refuses an abbreviation that someone else already has – then offer
another one. Validation must give 0 errors.

If the commit is stopped with "Commit zastaven / Commit stopped", the
pre-commit hook found validation errors in what is being saved: explain them
plainly, fix them with the user and commit again. Never bypass the hook
(`--no-verify`, changing `core.hooksPath`).

Save it according to the access from step 5 (in `<folder>`, after the
user's yes). Git needs a name and an e-mail for the history: if
`git config --global user.name` or `user.email` is empty, set them with
`git config --global` – the name from step 1 and, unless the user wants
another address, GitHub's private no-reply address from
`gh api user --jq '"\(.id)+\(.login)@users.noreply.github.com"'`.

- **0 – save directly** (admin or maintain):
  `git add repo.yaml`, `git commit -m "Add member <abbr> (<role>)"`,
  `git pull --rebase`, `git push`. If GitHub refuses the push (a protected
  branch), continue as with 2.
- **2 – through a pull request** (write):
  ```
  git switch -c member-<abbr>
  git add repo.yaml
  git commit -m "Add member <abbr> (<role>)"
  git push -u origin member-<abbr>
  gh pr create --base main --title "Add member <abbr>" --body "New family member <Full name> (<abbr>, <role>), added by /proavus:setup."
  git switch main
  ```
  Tell the user to send the link to the maintainer, who merges it. Until
  then the abbreviation is only on this computer: the first
  `/proavus:start` waits until the pull request is merged (`gh pr view
  member-<abbr> --json state`), then `git pull` and continue.
- **6 – read only**: nothing can be saved. Leave `repo.yaml` unchanged
  (`git checkout -- repo.yaml`) and tell the user to ask the maintainer for
  write access (Settings → Collaborators); then run `/proavus:setup` again.

## 7. Hand over

In a few lines: what is installed, where the family folder is, which GitHub
account is used, whether 2FA is on (only what the user told you), and the
state of the member (saved, or the pull request link).

Then: open a **new session in the family folder** (the Claude app, Code tab
– the folder is shown under the message box; never in the `proavus` folder)
and type `/proavus:start` as the first message; end every session with
`/proavus:end`. They never need git themselves. If something stops working,
`/proavus:setup` checks everything again.
