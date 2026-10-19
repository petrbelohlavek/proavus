# 0019 Generované výstupy se do gitu neukládají

- **Stav:** přijato (2026-10-20)
- **Původně:** R24

## Kontext

Při zápisu přímo do hlavní větve (ADR 0016) by ukládané výstupy způsobovaly konflikty a neustálé změny pod rukama.

## Rozhodnutí

`START-HERE`, mapa, GEDCOM a indexy nejsou v gitu (`.gitignore`). `START-HERE` vygeneruje `/start` lokálně, mapu a GEDCOM příkaz na požádání. Automatická úloha na GitHubu jen kontroluje, nic nezapisuje.

## Důsledky

Opravuje se vždy zdroj, výstup se přegeneruje.
