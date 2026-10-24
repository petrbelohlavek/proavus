# 0063 Sloučení zdvojených tvrzení: `merge_assertions.py`

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Upřesňuje:** [ADR 0040](0040-validator-advice-and-duplicates.md)
  (zdvojená tvrzení)

## Kontext

Validátor hlásil „spojit citace do jednoho tvrzení“, ale sloučení
neuměl navrhnout ani provést; ruční sloučení znamenalo přepsat citace,
najít všechny odkazy na rušené tvrzení (vztahy, sloučení osob, rozpory,
otázky, sezení) a soubor smazat. Navíc skupina stála jen na osobě, typu,
datu a hodnotě a místo přehlížela – radila tedy sloučit i dvě tvrzení se
stejným datem a jiným místem, což je rozpor, ne duplicita.

## Rozhodnutí

- Validátor: do skupiny patří jen tvrzení se stejným místem. Stejné místo
  je stejné ID místa, nebo stejný zápis místa, nebo ID místa a jedno z jeho
  jmen; tvrzení bez místa se k jakémukoli přidá. Stejné datum s jiným
  místem je varování „dvě verze: zapiš rozpor“, pokud ho už nepokrývá
  rozpor, který obě tvrzení jmenuje. Rada u duplicit obsahuje hotový příkaz.
- `tools/merge_assertions.py` (`tools/proavuslib/merge.py`), kopíruje se do
  `.proavus/`:
  - `plan REPO [ID …]` nic nemění: které tvrzení zůstane (zadané `--keep`,
    jinak to s nejvíce odkazy, jinak nejstarší ID), spojené citace (stejná
    citace jen jednou), spojené `tags`, `refs`, `schema_gap`, doplněné místo
    a soubory, jejichž odkazy se změní. Bez ID naplánuje všechny skupiny
    z validátoru.
  - **STOP** – nic se nezapíše, rozhoduje badatel: jiná osoba, typ, datum,
    hodnota nebo místo; jiná jistota (volba `--confidence`); jiné hodnocení
    téže citace; potvrzení (`confirmed`) na tvrzení, které by zmizelo;
    jiná hodnota dalšího pole; tvrzení o identitě (to se slučuje přes
    `aliases` a bránu identity).
  - `apply REPO ID …` až po souhlasu: citace do ponechaného tvrzení, tělo
    rušeného pod `## Merged from A-…`, odkazy v hlavičkách i v textu
    přepsané (bez opakování v seznamech), rušené soubory smazané (zůstávají
    v historii gitu), validace.
  - Rozpor, který jmenuje dvě slučovaná tvrzení, plán ukáže jako poznámku.
- Skill `start` nabídne plán, když validátor sloučení radí, a `apply`
  spustí jen na slovo uživatele.

## Důsledky

Přidání (minor verze, bez migrace). Nástroj nerozhoduje o obsahu: kde by
sloučení něco zvolilo, zastaví se. Hlavičky přepsaných souborů zapisuje
`frontmatter.join` – pořadí polí zůstává, formátování YAML se může drobně
změnit.
