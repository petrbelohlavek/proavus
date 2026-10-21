---
name: upgrade
description: Upgrade a Proavus family repository to the plugin's version (run as /proavus:upgrade) – show what changes, reinstall .proavus/, refresh the Proavus blocks and the check workflow, migrate data if needed, validate and save. Use when /proavus:start says the Proavus copy is older than the plugin.
disable-model-invocation: true
---

# Upgrade the family repository

Answer in the user's language, in plain words. The upgrade changes only the
framework's files in the family repository (ADR 0009): `.proavus/`, the
`<!-- proavus:begin/end -->` blocks in `CLAUDE.md` and `AGENTS.md`,
`.github/workflows/validate.yml`, `schema_version` (and, with the user's
answers, `map`) in `repo.yaml` – plus the data only if a migration is needed.
The family's own text and data are never touched otherwise.

## 1. Is this a family repository, and is it private?

As in `/proavus:start`: the folder must contain `repo.yaml`; if it is the
Proavus framework (`.claude-plugin/marketplace.json`, no `repo.yaml`), stop.

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private .
```

Exit 0 continue · 3 stop, do not write anything · 4 fix `gh` first · 5 no
remote yet: upgrade locally, commit, do not push.

## 2. Start from a clean, current state

`git status --short` must be empty. If not, the last session was not
finished: say so and offer `/proavus:end` first (the upgrade commit must
contain only the upgrade). Then `git pull --rebase` if there is a remote; on
a conflict stop and explain.

## 3. What would change

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" upgrade-plan .
```

- exit 1 – already current: say so and stop;
- exit 3 – cannot upgrade: the repository is newer than the plugin (update
  the plugin as in the README of Proavus, "Update to a new release":
  `git pull` on the `stable` branch of the framework folder,
  `claude plugin marketplace update proavus`, `claude plugin uninstall
  proavus@proavus`, `claude plugin install proavus@proavus`, new session)
  or a needed migration is missing – explain and stop, change nothing;
- exit 0 – an upgrade is available.

Summarise for the user in a few lines: from which version to which, what the
CHANGELOG sections bring that matters for the family (new commands, new
checks, new kinds of data), the schema changes, and whether the data will be
migrated (`migrate.py`). Do not paste the whole CHANGELOG.

## 4. Questions for new settings

If the plan says `repo.yaml has no map.root` (the family map, since 0.2.0):

- ask **whose ancestors the map should start from**. Offer the persons the
  plan lists as possible starting persons (nobody's parent yet – usually the
  youngest generation, often the researcher or their child); the user may
  name anyone else in `people/` (check the ID exists). It may also stay
  empty for now;
- if `map.lang` is missing: without it the map follows the region (`cz` →
  Czech, otherwise English); ask only whether that is right, and set it
  (`cs` or `en`) if they want it written down or different.

If the plan lists **marital status inside status_as_written**: offer to
split those participants after the upgrade
(`${CLAUDE_PLUGIN_ROOT}/method/reading-records.md` §4) – the marital words
into `marital_status_as_written` (and `marital_status` only when the record
states it clearly), the rest stays in `status_as_written`. It is optional,
nothing breaks without it; change a record only on the user's yes.

## 5. Confirm and upgrade

Show the plan once more in one line (versions, map answers) and continue
only after a clear yes:

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" upgrade . --map-root <P-ID> --map-lang <cs|en>
```

(leave out `--map-root` / `--map-lang` for questions the user skipped). The
tool reinstalls `.proavus/`, runs the migration if the major version
changed, refreshes the blocks and the workflow, sets `schema_version` and
`map`, and validates with the new copy.

- `WARN` lines (e.g. a missing Proavus block in `CLAUDE.md`) – explain;
  never create or rewrite the family's files without asking.
- Validation errors (exit 1) – the new version checks more than the old one.
  Explain each error plainly and fix it together with the user (the identity
  gate and living persons rules apply as always); commit only with 0 errors.

## 6. Save

1. `git status --short` – only `.proavus/`, `CLAUDE.md`, `AGENTS.md`,
   `.github/workflows/validate.yml`, `repo.yaml` and – after a migration –
   the migrated data files may have changed. Anything else: ask.
2. `git add -A`, then commit with the line the tool printed after
   `COMMIT:` and the versions of the CHANGELOG sections as the body, e.g.
   `git commit -m "Upgrade Proavus 0.1.0 → 0.3.0" -m "Proavus CHANGELOG: 0.2.0, 0.3.0"`.
3. `check-private` again, then `git push` (exit 0 only; exit 5: commit
   only).

## 7. Close

Two lines: the new version and what is new for the family (e.g. "the family
map: `uv run .proavus/tools/build_views.py .` → `views/mapa.html`"). Other
members get the upgrade with their next `/proavus:start` (git pull); their
own plugin must be at least this version.
