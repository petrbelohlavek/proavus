# 0041 Snímky z archivních portálů: jen kde to provozovatel dovolí, po souhlasu

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Bádání stojí na snímcích z portálů archivů (ARON, Acta Publica, Matricula).
Agent by je mohl stahovat sám, ale portály patří archivům, které určují
podmínky; a celé knihy do repa rodiny nepatří (ADR 0019, výřezy 300 kB).
Zjištěno 20. 10. 2026 z veřejných stránek portálů:

- **ARON** (Východočeské archivy): veřejné rozhraní (`/api/aron/apu/<id>/entity`
  s metadaty a seznamem snímků včetně velikosti, snímek
  `/api/aron/referencedfiles/<id>`), `robots.txt` bez omezení;
- **Acta Publica** (MZA): podmínky užití zakazují „zasahovat bez souhlasu
  Provozovatele do technické podstaty“ a publikovat snímky bez písemného
  souhlasu; `robots.txt` aplikace zakazuje vše;
- **Matricula Online**: `robots.txt` zakazuje automatický přístup ke stránkám
  snímků (`?pg=`) všem a robotům AI (výslovně i ClaudeBot) celý web.

## Rozhodnutí

`tools/archive_fetch.py` (jen standardní knihovna, ADR 0021):

- **ARON:** `book` (metadata), `list` (snímky a velikosti, nic nestahuje),
  `link`, `get --dry-run` a `get`. Stahuje jen do složky **mimo repozitář**
  (odmítne složku uvnitř gitu, repa rodiny i frameworku), nejvýš `--max`
  snímků na volání (výchozí 10, strop 50), s pauzou mezi snímky; ověří typ
  `image/jpeg`, velikost podle seznamu a úplný JPEG, jinak nic neuloží.
- **Acta Publica, Matricula:** jen `link` – odkaz na snímek v prohlížeči
  portálu; `book`, `list` a `get` odmítne (exit 3) a nic z portálu nečte.
  Zpřístupní se, až archiv souhlas dá (dotaz přes `inquiry`, ADR 0036).
- **Souhlas:** `/proavus:start` stahuje až po výslovném „ano“ badatele
  k seznamu z `get --dry-run`; jiným způsobem (automatizací prohlížeče)
  portály bez povoleného přístupu neprochází.

## Důsledky

Testy používají podvrženou síť a fiktivní odpovědi; na skutečné portály
nesahají. Když portál změní rozhraní nebo podmínky, mění se adaptér a tento
záznam (nový ADR). Obecné zkušenosti z bádání jsou v
`method/reading-records.md` a `regions/cz/pitfalls.md`.
