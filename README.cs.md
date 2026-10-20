<!-- source: README.md @ v0.2.0 -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/proavus-logo-dark.svg">
    <img src="brand/proavus-logo.svg" alt="Proavus" width="360">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>Čeština</b></p>

**Proavus** – rodokmen s AI podle důkazů, ne odhadů: metodika, datové schéma
a nástroje pro bádání s LLM podle Genealogical Proof Standardu.

> **Rozpracováno (0.2.0).** Existuje schéma, validátor, závazná pravidla
> a první příkazy (`/proavus:init`, `/start`, `/end`); průvodce instalací
> (`/setup`) zatím ne. Zatím není k běžnému použití.

## Jak to bude fungovat

1. Založte si účet na GitHubu a nainstalujte desktopovou aplikaci Claude.
2. Požádejte Clauda o nastavení Proavus – vše doinstaluje a založí vám vlastní
   **soukromé** repo rodiny. Nikdy nezapisujte data rodiny do forku Proavus:
   forky jsou veřejné.
3. Otevřete své soukromé repo a napište `/start`.
4. Popište, koho hledáte; Claude s vámi sestaví otázku a plán a provede vás
   čtením zápisů.
5. Napište `/end`: výsledky se uloží s citacemi zdrojů a zkontrolují.

## Mapa rodiny

`tools/build_views.py` vytvoří z repa rodiny jednu soběstačnou stránku HTML:
funguje offline, nic nenačítá z internetu a do gitu se neukládá. Ukázka je
z fiktivní testovací rodiny v `tests/fixtures/family/`. Barva karty ukazuje,
jak je osoba doložená, čára, jak jistý je vztah.

<p align="center"><img src="docs/images/map-tree.cs.png" alt="Mapa rodiny: strom předků ve sloupcích generací, karty obarvené podle doložení a čáry podle jistoty" width="800"></p>

Kliknutím na kartu se otevře detail se všemi údaji, jejich jistotou a zdrojem:

<p align="center"><img src="docs/images/map-detail.cs.png" alt="Detail osoby: údaje se zdroji, vztahy, otevřený rozpor a otázka" width="700"></p>

## Co tu je

| Část | Kde |
|---|---|
| Deset závazných pravidel | [method/rules.cs.md](method/rules.cs.md) |
| Čtení zápisů | [method/reading-records.md](method/reading-records.md) (anglicky) |
| Datové schéma v0 | [schema/](schema/README.md) |
| Validátor | `uv run tools/validate.py <repo-rodiny>` |
| Mapa rodiny | `uv run tools/build_views.py <repo-rodiny>` → `views/mapa.html` |
| Architektura a rozhodnutí | [docs/architecture.md](docs/architecture.md), [docs/decisions/](docs/decisions/) |

## Licence

| Část | Licence |
|---|---|
| Metodika a dokumentace (`method/`, `docs/`, `regions/`, README) | CC BY 4.0 |
| Kód (`tools/`, `tests/`, hooky, workflow) | MIT |
| Schéma, slovníky, šablona repa rodiny | CC0 1.0 |
| Název a logo (`brand/`) | všechna práva vyhrazena |

Podrobnosti v [`REUSE.toml`](REUSE.toml) a [`LICENSES/`](LICENSES/).
© 2026 Petr Bělohlávek a přispěvatelé Proavus.
