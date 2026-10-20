<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/proavus-logo-dark.svg">
    <img src="brand/proavus-logo.svg" alt="Proavus" width="360">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.cs.md">Čeština</a></p>

**Proavus** – evidence-first genealogy with AI: a method, a data schema and
tools for researching your family history with an LLM under the
Genealogical Proof Standard.

> **Work in progress (0.2.1).** The schema, the validator, the binding rules
> and the first commands (`/proavus:init`, `/proavus:start`,
> `/proavus:end`) exist; the guided setup (`/setup`) does not yet. Not ready
> for general use.

## How it will work

1. Create a GitHub account and install the Claude desktop app.
2. Ask Claude to set up Proavus – it installs everything and creates your
   own **private** family repository. Never put family data in a fork of
   Proavus: forks are public.
3. Open your private repository and type `/proavus:start`.
4. Describe who you are looking for; Claude helps you frame the question,
   plan the search and read the records.
5. Type `/proavus:end`: findings are saved with source citations and checked.

## Install the plugin from a local folder

Until Proavus is public, the plugin is installed from a local copy of this
repository: the repository is its own plugin catalogue
(`.claude-plugin/marketplace.json`, the whole repository is the plugin, ADR
0014). Needs Claude Code 2.1.275 or later (`claude --version`). The desktop
app (Code tab) and the `claude` command in a terminal share the same
settings, so you install once per computer – in a terminal.

1. **Get the framework** into a folder outside iCloud Drive, Dropbox,
   OneDrive or Google Drive, e.g.
   `git clone https://github.com/petrbelohlavek/proavus.git ~/Documents/Proavus/proavus`
   (private for now – you need access).
2. **Add the catalogue and install the plugin:**
   ```
   claude plugin marketplace add ~/Documents/Proavus/proavus
   claude plugin install proavus@proavus
   ```
3. **Check the installation:**
   - `claude plugin list` shows `proavus@proavus`, `Status: ✔ enabled`;
   - `claude plugin details proavus@proavus` shows `Skills (3)  end, init, start`.
4. **Check the commands in a session.** Sessions started before the
   installation do not see the plugin – start a new one:
   - **terminal:** run `claude` in any folder and type `/proavus:` – the
     suggestions offer `/proavus:init`, `/proavus:start` and `/proavus:end`;
   - **desktop app:** open a new session in the Code tab and type `/proavus:`
     in the message box – the same three commands appear.

   A quick check that changes nothing: in an empty folder run
   `claude -p "/proavus:start" --permission-mode plan` – Proavus answers that
   the folder is not a family repository yet and offers `/proavus:init`.
5. **Create your family repository** with `/proavus:init` (in a new session
   in the folder where it should live). It also forbids Claude Code's
   file-editing tools to touch the framework folder from the family
   repository (`.claude/settings.local.json` there).

**Update** after `git pull` in the framework folder:
`claude plugin marketplace update proavus`, then
`claude plugin update proavus@proavus` (it takes a new version number from
`.claude-plugin/plugin.json`), then start a new session.
**Remove:** `claude plugin uninstall proavus@proavus` and
`claude plugin marketplace remove proavus`.

The tools run straight from this folder (`${CLAUDE_PLUGIN_ROOT}` is the
folder itself), and Claude Code also copies the folder – including files git
ignores – into its plugin cache. Keep nothing private in the framework
folder.

## Using the commands

Type the commands in the message box of a Claude Code session (desktop app
or `claude` in a terminal): type `/proavus:` and pick one. What matters is
the **folder the session runs in** – it is shown under the message box.

| Command | When | Where | What it does |
|---|---|---|---|
| `/proavus:init` | once | a new session in the folder where the family repository should live, or in its empty clone | creates the **private** family repository from the template, installs `.proavus/`, protects the framework from edits, puts it on GitHub and checks it is private |
| `/proavus:start` | first message of every research session | a session in the family repository | privacy check, downloads others' work, overview (`START-HERE.md`), picks or writes the research question |
| `/proavus:end` | last message of every research session | the same session | session record with the next step, decisions only a human makes, validation (0 errors), saves to GitHub |

Never in the `proavus` framework folder: `/proavus:start` and
`/proavus:end` stop there, `/proavus:init` refuses a folder that is not
empty. Forgot one? `/proavus:start` can be run at any time; after a missed
`/proavus:end` open a session in the family folder and run it – the work is
still in the files, just not saved yet. Details for family members are in
the family repository's README.

## The family map

`tools/build_views.py` turns a family repository into one self-contained
HTML page: it works offline, loads nothing from the internet and is never
saved in git. Below is the fictional test family from `tests/fixtures/family/`.
Card colour shows how well each person is documented, the line shows how
sure each relationship is.

<p align="center"><img src="docs/images/map-tree.en.png" alt="Family map: ancestor tree in generation columns with cards coloured by evidence and lines by confidence" width="800"></p>

A click on a card opens the detail with every fact, its confidence and its
source:

<p align="center"><img src="docs/images/map-detail.en.png" alt="Person detail: facts with sources, relationships, open conflict and question" width="700"></p>

## What is here

| Part | Where |
|---|---|
| Ten binding rules | [method/rules.md](method/rules.md) |
| Reading records | [method/reading-records.md](method/reading-records.md) |
| Data schema v0 | [schema/](schema/README.md) |
| Validator | `uv run tools/validate.py <family-repo>` |
| Family map | `uv run tools/build_views.py <family-repo>` → `views/mapa.html` |
| Architecture and decisions | [docs/architecture.md](docs/architecture.md) (Czech for now), [docs/decisions/](docs/decisions/) |

## Licence

| Part | Licence |
|---|---|
| Method and documentation (`method/`, `docs/`, `regions/`, README) | CC BY 4.0 |
| Code (`tools/`, `tests/`, hooks, workflows) | MIT |
| Schema, vocabularies, family repository template | CC0 1.0 |
| Name and logo (`brand/`) | all rights reserved |

Details in [`REUSE.toml`](REUSE.toml) and [`LICENSES/`](LICENSES/).
© 2026 Petr Bělohlávek and Proavus contributors.
