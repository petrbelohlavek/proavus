# 0026 Oddělení vývoje frameworku od dat rodiny

- **Stav:** přijato (2026-10-20)
- **Původně:** kap. 14 návrhu

## Kontext

Správce vyvíjí framework a zároveň bádá ve vlastní rodině; data rodiny se nesmí dostat do frameworku, který bude veřejný.

## Rozhodnutí

Dvě oddělené session v Claude Code: výzkum (rodinné repo; framework jen ke čtení) a framework (rodinné repo zakázáno v `.claude/settings.local.json`). Seznam jmen rodiny je v souboru mimo obě repa (`Proavus/.guard-names`, lze změnit proměnnou `PROAVUS_GUARD_NAMES`). Git hooky `pre-commit` a `commit-msg` (`.githooks/`, zapnout `git config core.hooksPath .githooks`) zablokují commit se jménem ze seznamu; chybí-li seznam, commit se zablokuje. Výjimky (jméno autora) jsou v `.guard-allow`. Příklady ve frameworku jsou vždy smyšlené.

## Důsledky

Kontrola běží jen lokálně – seznam jmen nikdy neopouští počítač správce. Před zveřejněním se navíc prohledá celá historie (architektura, kap. 11).
