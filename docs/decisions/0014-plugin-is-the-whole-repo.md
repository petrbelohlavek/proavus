# 0014 Plugin = celé repo; kopie nástrojů v `.proavus/`

- **Stav:** přijato (2026-10-20)
- **Původně:** R19

## Kontext

Nástroje mají mít všichni členové i automatická kontrola na GitHubu bez tajných klíčů; skilly mají odkazovat na metodiku, ne ji kopírovat.

## Rozhodnutí

Celé repo `proavus` je plugin: `.claude-plugin/marketplace.json` s `"source": "."` a `.claude-plugin/plugin.json` v kořeni. Skilly odkazují na metodiku přes `${CLAUDE_PLUGIN_ROOT}`. Do rodinného repa se ukládá připnutá kopie nástrojů, schématu a slovníků v `.proavus/` (spravuje `/upgrade`). Výstupy a nastavení mapy jsou v rodinném repu, program ve frameworku.

## Důsledky

Rodinné repo je soběstačné (validace v CI bez přístupu k soukromému frameworku). Nástroje počítají se stejným rozložením v `proavus/` i `.proavus/` (`tools/`, `schema/`, `regions/*/schema-ext.yaml`). `CLAUDE.md` v kořeni pluginu se nenačítá (validátor pluginu jen varuje).
