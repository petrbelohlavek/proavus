# 0042 Převod staršího bádání plánem: klíče, odkazy @klíč, kontrola celé dávky

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Rodiny přichází se staršími poznámkami, deníkem hledání a stromem. Ručně
zakládat desítky souborů s ID a vzájemnými odkazy je pracné a chybové;
vlastní skripty rodina psát nemá (a neměla by – každý by zapisoval jinak).

## Rozhodnutí

- **Plán** (YAML): seznam entit se symbolickým `key` místo ID; odkazy
  `@klíč` v hlavičce (celý řetězec i uvnitř věty) a v těle; `slug` pro název
  souboru; `body`. Volitelně `diary:` – záznamy starého deníku – a u entit
  `from_diary:`.
- **`proavuslib/bulk.py`** (`Batch`: `add`, `add_diary`, `files`,
  `preview`, `write`) dá každé entitě nové ID (`ids.new_id`), nahradí
  odkazy a zapíše soubory stylem ručního zápisu (`frontmatter.join`, ADR
  0030) do správné složky (sezení do `sessions/RRRR/`).
- **Celá dávka, nebo nic:** zapíše se jen tehdy, když dočasná kopie repa
  s dávkou projde validátorem bez chyb, každý záznam deníku má odkaz a žádný
  soubor neexistuje.
- **Klíče se pamatují** v `archive/import-keys.yaml`: pozdější plán odkazuje
  na klíče dřívějšího; klíč jde použít jen jednou.
- **Původní text deníku** se vloží do těla souborů, které na něj odkazují
  (`## From the old research diary`) – po převodu je dohledatelný.
- `tools/bulk_import.py` je tenký obal (`--dry-run`), kopíruje se do
  `.proavus/`; postup v `docs/import.md`: archiv → pilotní otázka → zbytek →
  denní sezení z deníku → kontrola odkazů deníku.

## Důsledky

Převod nezvyšuje jistotu: co staré poznámky tvrdí, je nejvýš `possible`,
dokud zápis neprojde druhým čtením a branou identity. Plán je jednorázový
pracovní soubor; do repa se ukládá výsledek (a mapa klíčů v `archive/`).
