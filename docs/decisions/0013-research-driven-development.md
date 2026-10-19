# 0013 Vývoj řízený vlastním výzkumem

- **Stav:** přijato (2026-10-20)
- **Původně:** R18

## Kontext

Framework navržený naslepo by řešil nepodstatné a míjel skutečné potřeby.

## Rozhodnutí

Framework roste jen podle potřeb skutečného bádání; data rodiny správce jsou integrační test; výzkum a vývoj probíhají v oddělených session (ADR 0026). Žádné funkce do zásoby.

## Důsledky

Každá změna má důvod ve výzkumu; z reálných problémů vznikají fiktivní testovací případy. Vydání po dávkách.
