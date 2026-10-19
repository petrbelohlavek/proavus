# 0002 Jádro nezávislé na modelu, Claude Code jako hlavní adaptér

- **Stav:** přijato (2026-10-20)
- **Původně:** R2

## Kontext

Rodiny pracují přes Claude, ale metoda má vydržet déle než jeden nástroj a fungovat i s jinými modely.

## Rozhodnutí

Metodika, schéma a nástroje nezávisí na modelu (`method/`, `schema/`, `tools/`). Plugin pro Claude Code je hlavní adaptér; pro jiné nástroje slouží `AGENTS.md` a chatový adaptér.

## Důsledky

Plugin je pohodlí, ne podmínka. Pravidla jsou v souborech, ne v promptu. Evaly ověřují chování napříč modely.
