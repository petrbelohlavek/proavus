# 0015 Rozšiřitelné schéma ve čtyřech vrstvách

- **Stav:** přijato (2026-10-20)
- **Původně:** R20

## Kontext

Genealogie má nekonečně druhů údajů a regionálních zvláštností (podoby jmen, vyznání, typy vztahů, čísla domů, panství). Pevná pole by vyžadovala neustálé změny schématu.

## Rozhodnutí

Čtyři vrstvy: (1) malé pevné jádro, (2) slovníky hodnot, (3) regionální rozšíření zapínaná v `repo.yaml`, (4) záchranná síť `schema_gap`. Fakta jsou tvrzení s typem, ne pevná pole. Přidání = menší verze bez převodu dat; zásadní změna = hlavní verze + `migrate.py`. Validátor neznámou hodnotu slovníku jen ohlásí, neznámé pole odmítne.

## Důsledky

Schéma v0 obsahuje středoevropské potřeby: podoby jmen, vyznání, podtypy vztahů; rozšíření `cz` (číslo popisné, panství).
