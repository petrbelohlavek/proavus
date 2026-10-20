# 0035 Hledání v databázi zapsané dotazem

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Databáze a rejstříky na portálech se prohledávají dotazem, ne listováním po stranách; rozsah se pak nedá vyjádřit jako `dates` nebo `pages` a negativ bez přesného dotazu nic neříká.

## Rozhodnutí

Rozsah v `coverage.ranges` smí místo `dates`/`pages` mít `query` – dotaz tak, jak byl zadán (pole, hodnoty, filtry). Jen dotazem (bez dat a stran) smí být rozsah u metod `database-search`, `full-text-search` a `index`; jinak validátor chybu ohlásí.

## Důsledky

Jádro, přidání. Upozornění „rejstřík není důkaz nepřítomnosti“ u `index` platí dál.
