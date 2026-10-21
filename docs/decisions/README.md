# Rozhodnutí frameworku (ADR)

Krátké samostatné záznamy: kontext, rozhodnutí, důsledky. Změna rozhodnutí = nový záznam, který starý nahradí; historie se nepřepisuje.
Sloupec *Původně* odkazuje na číslování rozhodnutí v pracovním návrhu architektury (v1.22).

| # | Rozhodnutí | Stav | Původně |
|---|---|---|---|
| [0001](0001-two-repositories.md) | Dvě repa: framework a soukromé repo rodiny | přijato | R1 |
| [0002](0002-model-independent-core.md) | Jádro nezávislé na modelu, Claude Code jako hlavní adaptér | přijato | R2 |
| [0003](0003-github-free-pilot-and-target.md) | GitHub zdarma: pilot na osobním účtu, cílově organizace s modelem forků | přijato | R3, R4, R13 |
| [0004](0004-markdown-yaml-source-of-truth.md) | Zdroj pravdy je Markdown + YAML v gitu | přijato | R8 |
| [0005](0005-machine-llm-human.md) | Princip práce: stroj → LLM → člověk | přijato | R9 |
| [0006](0006-own-storage-later.md) | Dlouhodobě vlastní úložiště a sdílení mezi rodinami | navrženo | R10 |
| [0007](0007-name-and-brand.md) | Název Proavus a logo | přijato | R11 |
| [0008](0008-repository-names.md) | Názvy rep: `proavus` a `proavus-<rodina>` | přijato | R12 |
| [0009](0009-init-and-upgrade.md) | Rodinné repo zakládá `/init` a aktualizuje `/upgrade` | přijato | R14 |
| [0010](0010-private-until-phase-4.md) | Obě repa začínají jako soukromá; framework se zveřejní ve fázi 4 | přijato | R15 |
| [0011](0011-installation-and-uv.md) | Instalace: aplikace Claude + `/setup`; nástroje přes `uv` | přijato | R16 |
| [0012](0012-licences-by-part.md) | Licence podle částí repa, označení REUSE | přijato | R17 |
| [0013](0013-research-driven-development.md) | Vývoj řízený vlastním výzkumem | přijato | R18 |
| [0014](0014-plugin-is-the-whole-repo.md) | Plugin = celé repo; kopie nástrojů v `.proavus/` | přijato | R19 |
| [0015](0015-extensible-schema.md) | Rozšiřitelné schéma ve čtyřech vrstvách | přijato | R20 |
| [0016](0016-pilot-without-reviewers-identity-gate.md) | Pilot bez schvalovatelů; brána identity v sezení | přijato | R21, R4 |
| [0017](0017-record-participants.md) | Účastníci zápisu jsou oddělení od osob | přijato | R22 |
| [0018](0018-single-semantic-version.md) | Jedna sémantická verze pro celé repo | přijato | R23 |
| [0019](0019-generated-outputs-not-in-git.md) | Generované výstupy se do gitu neukládají | přijato | R24 |
| [0020](0020-research-chronicle.md) | Kronika výzkumu | přijato | R25 |
| [0021](0021-tool-dependencies.md) | Nástroje smí mít připnuté závislosti (PyYAML, jsonschema) | přijato | — |
| [0022](0022-evidence-axes-and-confidence.md) | Dvě osy: hodnocení důkazů a jistota závěru | přijato | — |
| [0023](0023-citation-locator.md) | Citace s povinným lokátorem | přijato | — |
| [0024](0024-collision-free-ids.md) | ID bez kolizí | přijato | — |
| [0025](0025-living-persons.md) | Žijící osoby | přijato | — |
| [0026](0026-separating-development-from-family-data.md) | Oddělení vývoje frameworku od dat rodiny | přijato | kap. 14 návrhu |
| [0027](0027-family-map.md) | Mapa rodiny jako jeden soběstačný soubor HTML | přijato (rozvržení nahrazeno 0028) | — |
| [0028](0028-family-map-layout.md) | Rozvržení mapy rodiny: sloupce generací, karty a detail v dialogu | přijato | — |
| [0029](0029-family-map-facts-and-sharing.md) | Mapa rodiny: data slovy, výběr údaje, žijící a sdílení | přijato | — |
| [0030](0030-migrations-in-minor-versions.md) | Migrace i v menších verzích: sjednocení dat | přijato | — |
| [0031](0031-record-crops.md) | Více výřezů u zápisu | přijato | — |
| [0032](0032-record-annotations.md) | Pozdější poznámky na okraji zápisu | přijato | — |
| [0033](0033-reading-by-agent-and-human.md) | Čtení agentem a člověkem; potvrzuje jen člověk, který zápis četl | přijato | — |
| [0034](0034-oral-speakers.md) | Více mluvčích ústního svědectví | přijato | — |
| [0035](0035-coverage-query.md) | Hledání v databázi zapsané dotazem | přijato | — |
| [0036](0036-inquiry-entity.md) | Dotazy na úřady jako entita `inquiry` | přijato | — |
| [0037](0037-human-tasks-with-status.md) | Úkoly pro člověka se stavem | přijato | — |
| [0038](0038-relationship-citations.md) | Přímé citace u vztahu | přijato | — |
| [0039](0039-start-here-readable.md) | START-HERE: jména místo ID, souhrn po otázkách, jen otevřené úkoly | přijato | — |
| [0040](0040-validator-advice-and-duplicates.md) | Validátor: přijatý negativ z rejstříku, pohlaví u identity, duplicity, rady | přijato | — |
| [0041](0041-archive-portals.md) | Snímky z archivních portálů: jen kde to provozovatel dovolí, po souhlasu | přijato | — |
| [0042](0042-bulk-import.md) | Převod staršího bádání plánem: klíče, odkazy @klíč, kontrola celé dávky | přijato | — |
| [0043](0043-pinned-actions.md) | Akce GitHubu připnuté na commit, minimální oprávnění, Dependabot | přijato | — |
| [0044](0044-roles-spouse-parents-grandparents.md) | Role účastníků: rodiče manžela/manželky, děd a babička bez strany | přijato | — |
| [0045](0045-edtf-unspecified-digits.md) | EDTF: jednotlivá nespecifikovaná číslice v měsíci a dni | přijato | — |
| [0046](0046-marital-status.md) | Rodinný stav účastníka jako samostatné pole | přijato | — |
| [0047](0047-tasks-per-question.md) | Úkol patří k otázce; poslední sezení jen z práce na otázce | přijato | — |
| [0048](0048-setup-for-family-members.md) | Průvodce `/proavus:setup` pro člena rodiny | přijato | — |
| [0049](0049-pre-commit-validation.md) | Validace před každým commitem v rodinném repu (hook `pre-commit`) | přijato | — |

Nové záznamy: `NNNN-kratky-nazev.md`, další volné číslo, stejná struktura.
