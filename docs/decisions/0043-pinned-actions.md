# 0043 Akce GitHubu připnuté na commit, minimální oprávnění, Dependabot

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Workflow frameworku (`ci.yml`) i rodinného repa (`validate.yml`) používaly
akce podle tagu (`actions/checkout@v4`, `astral-sh/setup-uv@v6`). Tag se dá
přesunout na jiný commit – kdo ovládne repozitář akce, spustí svůj kód
v našem workflow. V rodinném repu by to byl kód s přístupem k datům rodiny.

## Rozhodnutí

- **Připnutí na commit SHA** s komentářem verze, např.
  `actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0`,
  `astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0`
  (nejnovější vydání řad v4 a v6, ověřeno 20. 10. 2026 přes API GitHubu
  i `git ls-remote`). Nové hlavní verze (checkout v7, setup-uv v10) přijdou
  jako návrh Dependabotu, ne tiše.
- **Minimální oprávnění:** `permissions: {}` na úrovni workflow, úloha jen
  `contents: read`; `actions/checkout` s `persist-credentials: false`, aby
  token nezůstal v konfiguraci gitu pro další kroky.
- **Dependabot** (`.github/dependabot.yml`) jen pro GitHub Actions ve
  frameworku: týdně, jedna skupina, sedm dní odstup od vydání (`cooldown`) –
  čerstvě vydaná, ještě nevyzkoušená verze nepřijde hned.
- **Rodinné repo Dependabot nemá:** jeho workflow je soubor frameworku, který
  obnovuje `/proavus:upgrade` (ADR 0009); návrhy změn v rodinném repu by
  upgrade přepsal. Šablona má stejné připnutí jako framework (hlídá test) a
  rodiny ho dostanou s novou verzí Proavus.

## Důsledky

Aktualizace akcí = PR od Dependabotu ve frameworku; tentýž commit upraví
i šablonu (`templates/family/.github/workflows/validate.yml`), jinak test
selže. `tests/test_workflows.py` hlídá připnutí, shodu se šablonou,
oprávnění a `persist-credentials`.
