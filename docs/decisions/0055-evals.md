# 0055 Evaly: úlohy pro agenta na fiktivní rodině, hodnocení skriptem

- **Stav:** navrženo (2026-10-21)
- **Původně:** —

## Kontext

ADR 0002 slibuje, že evaly ověřují chování napříč modely, a architektura
(§2, kap. 11) chce před zveřejněním v README poctivě uvést, na kterých
modelech je postup otestovaný a s jakým výsledkem. Testy v `tests/` hlídají
nástroje, ne to, co agent v sezení skutečně udělá: jestli převezme rok
z indexu, spojí jmenovce, nebo poslechne text v záznamu. Zvažováno:
hodnocení jiným modelem (levné na psaní, ale samo nejisté), ruční hodnocení
(drahé, neopakovatelné), deterministické kontroly souborů po práci agenta.

## Rozhodnutí

- **Složka `evals/`** ve frameworku (do `.proavus/` se nekopíruje): úlohy
  `evals/tasks/<id>/`, sdílený kód `evals/evalkit.py`, nástroj
  `tools/eval.py` (`list`, `prepare`, `grade`, `run`).
- **Pracovní prostor** = fiktivní testovací rodina + `AGENTS.md`
  a `CLAUDE.md` ze šablony + `.proavus/` + soubory úlohy. Archivní portál
  nahrazuje `portal/<ID pramene>/` – stránky přepsané jako text, jeden
  soubor na snímek. Agent nedostane nic navíc proti skutečnému sezení;
  badatel „není k dispozici“, takže co patří člověku, musí nechat jemu.
- **Hodnocení skriptem** porovnáním před a po: společné kontroly (validace
  bez chyb, žádné nové potvrzení agentem, nic smazáno, `.proavus/`,
  `portal/` a nastavení nezměněny) a kontroly úlohy v `grade.py`. Žádný
  model nehodnotí jiný.
- **Každá úloha má referenční řešení:** `reference/pass/` musí projít,
  `reference/fail-*/` (typická chyba) musí selhat v kontrolách z
  `_expect.txt`, a nicnedělání musí selhat – hlídá `tests/test_evals.py`.
  Tak se ověřuje hodnotitel bez volání modelu.
- **Spuštění** `eval.py run … --agent "<příkaz>" --times N`: příkaz dostane
  zadání na vstupu a běží v pracovním prostoru, takže jde použít Claude Code
  (`claude -p`) i jiného agenta. Výsledek je počet úspěšných pokusů;
  `--save` ho uloží do `evals/results/`.
- **První tři úlohy** podle pravidel, která stroj sám neuhlídá:
  `index-is-not-the-record` (pravidla 2, 3, 6, 7; past rejstříku z
  `regions/cz/pitfalls.md`), `namesakes` (4, 5), `data-not-instructions`
  (3, 7, 10).

## Důsledky

- Čtení rukopisu (pravidlo 3 na skutečných snímcích) zatím chybí: potřebuje
  skutečné snímky matrik a ty obsahují skutečné osoby. Které smí do
  veřejného repa (cizí, dávno zesnulí, s licencí archivu), rozhodne
  samostatné ADR.
- Běh evalů stojí volání modelu; v CI se pouští jen `tests/test_evals.py`
  (hodnotitelé), ne agent.
- Kontroly jsou úmyslně úzké (konkrétní záznam, datum, vazba); co nejde
  ověřit strojem (kvalita zdůvodnění), evaly neměří.
- Stav se změní na „přijato“ po prvním zaznamenaném běhu; výsledky pak
  patří do `TECHNICAL.md` (model, verze Proavus, úspěšnost).
- Nová úloha vzniká z chyby viděné ve skutečném bádání (ADR 0013).
