<!-- source: import.md @ v0.3.0 -->
# Převod staršího bádání do Proavus

Většina rodin něco má: sešit s hledáním, poznámky v textovém editoru, strom
nakreslený strýcem, genealogický program. Tento návod to převede na soubory
Proavus bez vlastních skriptů – Claude napíše **plán** (jeden soubor YAML),
`tools/bulk_import.py` ho zkontroluje a soubory založí.

Úplný fiktivní příklad je v [`examples/import/`](../examples/import/): staré
poznámky (`old-notes.md`), pilotní plán (`01-pilot.yaml`) a zbytek
(`02-rest.yaml`).

## Postup, který funguje

1. **Nejdřív archiv.** Starý materiál zkopírujte beze změny do `archive/`
   (exporty, skeny sešitu, soubor stromu). Zůstane zmrazený: nové soubory na
   něj odkazují, nikdo ho neupravuje. I při nedokonalém převodu se nic
   neztratí.
2. **Pilotní otázka.** Vyberte jednu otázku, na kterou staré poznámky skoro
   odpovídají (např. „Kdy zemřel Václav?“), a převeďte jen to, co k ní patří:
   zdroje, zápisy s přepisy, osoby, tvrzení a vztahy, prohledávání
   (`coverage`) a sezení. Výsledek zkontrolujte společně – `validate.py`,
   `START-HERE.md`, mapa rodiny. Postup upravte, než převedete víc.
3. **Zbytek** po dávkách stejného tvaru. Pozdější plán odkazuje na to, co
   založil dřívější (`@jan`), klíče se pamatují.
4. **Denní sezení z deníku.** Každý den starého deníku je jedno `session`
   (`sessions/RRRR/`, datum dne hledání) s tím, co se prohledalo (`coverage`),
   našlo (`records`), a s dalším krokem, jak byl tehdy zapsán.
5. **Kontrola, že každý záznam deníku má odkaz.** Každý záznam starého deníku
   je v plánu (`diary:`) a odkazuje na něj aspoň jeden nový soubor
   (`from_diary:`). Nástroj odmítne zapsat, dokud některý chybí, a původní
   text vloží do těla souborů, které na něj odkazují.

V sezení: „Pomoz mi převést staré poznámky podle
`${CLAUDE_PLUGIN_ROOT}/docs/import.md`.“ Claude projde archiv, navrhne pilotní
plán, ukáže zkoušku nanečisto a zapíše až po vašem „ano“.

## Plán

Viz anglická verze ([import.md](import.md#the-plan)) – klíče `key`, `type`,
`slug`, `body`, `from_diary`; odkazy `"@klíč"` (v YAML v uvozovkách) i v těle a
ve větách; ID se nikdy nepíše, vznikne nové; sezení jdou do
`sessions/<rok data>/`.

## Spuštění

```
uv run .proavus/tools/bulk_import.py plan.yaml --dry-run
uv run .proavus/tools/bulk_import.py plan.yaml
```

- `--dry-run` ukáže soubory, chyby a varování validátoru a záznamy deníku bez
  odkazu – a nic nezapíše.
- Bez něj se soubory zapíšou, jen když **celá dávka** nemá chybu, každý
  záznam deníku má odkaz a žádný soubor ještě neexistuje. Jinak se nezapíše
  nic.
- Klíče a jejich ID jsou v `archive/import-keys.yaml`; pozdější plán na ně
  může odkazovat. Klíč jde použít jen jednou.

## Co převod nesmí

- **Nezvyšovat jistotu.** „Otec byl Václav“ ze starých poznámek je `possible`,
  dokud se zápis znovu nepřečte (`read-once`) a v sezení neprojde branou
  identity (ADR 0016). Zapište, co staré poznámky tvrdí, citujte archiv a co
  schéma zatím neumí, dejte do `schema_gap`.
- **Nevymýšlet zdroje.** Údaj ze stromu bez zdroje zůstane bez citace (a
  `possible`), se `schema_gap` nebo otázkou.
- **Žijící osoby**: jen jméno, pohlaví, narození a vztahy (pravidlo 9) – starý
  strom jich mívá víc; nechte je v `archive/`, nepřevádějte.
- **Žádný negativ bez rozsahu.** „Nenalezeno“ z deníku je `coverage` s knihou,
  roky, stranami a hledanými jmény – nebo zůstane v citaci deníku, když je
  neznáme.
