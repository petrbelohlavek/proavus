# 0039 START-HERE: jména místo ID, souhrn po otázkách, jen otevřené úkoly

- **Stav:** přijato (2026-10-20)
- **Původně:** —
- **Upřesňuje:** [ADR 0037](0037-human-tasks-with-status.md)

## Kontext

START-HERE je první, co badatel a agent v sezení čtou. Ukazoval holá ID
(`R-…`, `X-…`), otázky jako tabulku bez souvislostí a úkoly zadané textem ze
všech sezení – takové úkoly nejdou uzavřít, takže by tam zůstaly navždy.

## Rozhodnutí

- U každého ID je jméno osoby, titul otázky, zápis slovy (událost, datum,
  místo, hlavní osoba), u rozporu čeho se týká, u dotazu adresát a předmět
  (`proavuslib/labels.py`); ID zůstává v závorce.
- **Souhrn po otázkách** místo tabulky: stav a kdo ji má, o kom je, kolikrát
  a s jakým výsledkem se hledalo, nalezené zápisy, poslední sezení a jeho
  další krok, otevřené rozpory o jejích osobách, neuzavřené dotazy, otevřené
  úkoly a plánované zdroje.
- **Úkoly:** se stavem (ADR 0037) otevřené ze všech sezení; zadané textem
  jen z posledního sezení. Totéž platí pro mapu.
- START-HERE vypisuje i prvních deset varování validátoru – radí, co doplnit.

## Důsledky

START-HERE je delší, ale čte se bez otevírání souborů. Staré textové úkoly
převede migrace 0.3.0 na otevřené úkoly se stavem (ADR 0030); pak se ukazují
všechny, dokud je někdo neuzavře.
