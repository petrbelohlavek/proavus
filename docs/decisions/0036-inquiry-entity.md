# 0036 Dotazy na úřady jako entita `inquiry`

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Dopisy a žádosti úřadům, archivům a farám trvají týdny a měsíce. V `human_tasks` byly jen jako text: chyběl stav, datum odeslání, odpověď a vazba na zápisy, které z odpovědi vznikly.

## Rozhodnutí

Nová entita `inquiry` (`IN-…`, složka `inquiries/`): `addressee`, `address`, `subject`, `sent`, `by`, `reference`, `status` (`sent` → `acknowledged` → `answered` → `closed`) s daty `acknowledged`, `answered`, výsledek `result`, navázané `records`, `questions`, `sources`. Zodpovězený dotaz potřebuje datum a výsledek, uzavřený výsledek; data jdou po sobě a nejsou v budoucnu. Sezení odkazuje `inquiries`, coverage s metodou `inquiry` pole `inquiry`. START-HERE a mapa ukazují neuzavřené dotazy.

## Důsledky

Jádro, nová entita (14. typ). Dopis i odpověď patří do těla souboru; pravidlo 9 platí i pro ně.
