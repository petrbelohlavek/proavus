# 0031 Více výřezů u zápisu

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Zápis má často víc částí, které je třeba doložit: vlastní zápis, poznámku na okraji, podpis, pokračování na další stránce. Pole `crop` uneslo jen jeden výřez.

## Rozhodnutí

`record.crops`: seznam `{path, caption}` (cesta vůči souboru zápisu, popis, co výřez ukazuje). `crop` zůstává jako zkratka pro jeden výřez; obě pole zároveň nejdou. Validátor ověří, že každý výřez existuje. Migrace 0.3.0 převede `crop` na `crops` (ADR 0030).

## Důsledky

Jádro (vrstva 1), přidání; nástroje berou výřezy přes `RepoValidator.crops()`.
