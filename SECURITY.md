# Security and privacy

Proavus handles family research, including data about living people. A
problem that could expose that data is as serious as a classic security
bug.

## What to report

- A tool, hook or workflow that runs unexpected code, leaks a token or can
  be abused through a crafted file, record or web page.
- Anything that could move family data out of a private family repository:
  into the public framework, into a shared family map, into logs or into
  a third-party service.
- A living person shown where the method says they must be hidden
  (for example in a map shared outside the family).
- Real family data that has appeared in this public repository – its
  files, history, issues or pull requests.

## How to report

**Never in a public issue.** Use GitHub's private reporting:
[Report a vulnerability](https://github.com/petrbelohlavek/proavus/security/advisories/new)
(the *Security* tab → *Report a vulnerability*). Only the maintainer sees
the report.

Describe the problem with made-up data; never attach real records, family
files or tokens. If real data or a token has already leaked, say where –
not what it is.

Proavus is a small volunteer project: expect an answer within about a
week. Once a fix is released on `stable`, the report may be published as
an advisory, crediting you if you wish.

## Supported versions

Only the latest release – the `stable` branch – gets fixes. Families
update with `/proavus:upgrade`.
