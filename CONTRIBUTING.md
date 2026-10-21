# Contributing to Proavus

Thank you for helping. Proavus is the public framework – method, data
schema, tools and plugin – that families copy into their own private
repositories. Everything here is public, so one rule comes before all the
others.

## Never share real family data

Not in an issue, a pull request, a comment, a commit, a screenshot or a
test – not even "just as an example". That means no real names, dates,
places tied to a person, transcripts, record images or notes of any real
family, yours included. Living relatives above all.

Describe the situation instead, with made-up people: *"a baptism where the
godfather is also the grandfather"*, *"a marriage record from 1850 with the
bride's domicile in another parish"*. Fictional test data are in
[`tests/fixtures/family/`](tests/fixtures/family/); add to them when you
need a case.

If you posted real data by mistake, edit or delete it at once and tell the
maintainer through a [private report](SECURITY.md) – edit history on GitHub
can still show the old text.

## What to contribute

Proavus grows from real research ([ADR 0013](docs/decisions/0013-research-driven-development.md)):
every change has a reason in a situation someone met while researching.
No features in advance.

- **A problem with a tool, the validator or the plugin** → an issue
  *Bug*.
- **Something your research needed** – a record type the schema cannot
  hold, a pitfall of a register or archive, a portal → an issue
  *Research need*. Say what you were doing, what you expected and what
  happened, with made-up people.
- **A security or privacy problem** → never an issue; see
  [SECURITY.md](SECURITY.md).
- **Translations of the method** (`method/*.<lang>.md`) are welcome;
  English is the source.

For anything bigger than a fix, open an issue first, so we can agree on
the approach before you write the code.

## Working on the code

You need Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) and git. The
rules for people and agents working here are in [AGENTS.md](AGENTS.md);
in short:

1. **Turn on the hooks:** `git config core.hooksPath .githooks`. They block
   names from a guard list kept **outside** the repository:
   `../.guard-names` next to your clone, or the path in
   `PROAVUS_GUARD_NAMES`. Write your own relatives' surnames and given
   names into it, one per line – then they cannot slip into a commit. The
   list is never committed and never printed.
2. **Tests:** `uv run python -m unittest discover -s tests`
3. **Licences:** `uvx --from 'reuse[charset-normalizer]==6.2.0' reuse lint`
4. **Changes of the method that a machine can check** go into
   `tools/validate.py`, with a test on fictional data.
5. **Schema:** a new kind of information is a new vocabulary value or a
   regional extension, not a new core field
   ([ADR 0015](docs/decisions/0015-extensible-schema.md)).
6. **Record the change** in `CHANGELOG.md`; a decision gets a new record in
   [`docs/decisions/`](docs/decisions/) (Czech for now – write in English
   if you prefer, it will be translated).

Code, schema fields and commands are in English; file names ASCII; hooks
and scripts in Python, never Bash (they must run on Windows).

Pull requests go to `main`. `stable` holds the last release and moves only
with a new version.

## Licence of contributions

By contributing you agree that your contribution is published under the
licence of the part it belongs to ([REUSE.toml](REUSE.toml)): MIT for code,
CC BY 4.0 for the method and documentation, CC0 1.0 for the schema,
vocabularies and template. The name and logo in `brand/` are not open for
reuse.

## Conduct

Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md).
