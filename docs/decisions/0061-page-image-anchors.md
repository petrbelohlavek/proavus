# 0061 Strana → snímek z kotev: `source.image_map`

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Doplňuje:** [ADR 0023](0023-citation-locator.md) (lokátor),
  [ADR 0058](0058-source-volumes.md) (svazky)

## Kontext

Portály číslují snímky, kniha strany nebo folia. Vztah se liší kniha od
knihy (jedna strana nebo dvě na snímek, vložené listy, chybějící či dvojité
skeny) a mění se i uvnitř jedné knihy. Vzorce typu „strana = 2 × snímek − 2“
platí jen pro knihu, ze které vznikly. Metoda chtěla dvě kotvy, ale psaly se
volně do sezení, takže je nástroje neznaly a s dalším sezením se ztrácely.

## Rozhodnutí

- `source.image_map`: seznam map, nejvýš jedna na svazek (`volume`) a jedna
  pro celý zdroj; `unit` `page` (výchozí) nebo `folio`; aspoň dvě kotvy
  `{page | folio, image, by, on, note}` – číslo přečtené na snímku, kdo
  a kdy ho přečetl. Kotva je pozorování, nikdy výpočet.
- Výpočet (`tools/proavuslib/imagemap.py`): mezi dvěma sousedními kotvami
  jen při pravidelném kroku – k snímků na stranu (0, 1, 2 …) nebo m stran na
  snímek; jinak je mezi kotvami zlom a je potřeba další kotva. Mimo kotvy jen
  odhad. Folio se počítá po stranách listu (23r, 23v).
- `tools/locate.py <SO-ID> --page N [--volume V]` vypíše snímek, na čem
  výsledek stojí a příkaz `archive_fetch.py link` pro portál; kód 0 jen pro
  přesný výsledek nebo výpočet mezi kotvami. Kopíruje se do `.proavus/`.
- Validátor: kotvy na stejné straně nebo snímky jdoucí zpět jsou chyba, dvě
  mapy pro jeden svazek a mapa svazku, který zdroj neuvádí, také. Každý
  záznam se stranou (foliem) a snímkem se porovná s mapou; nesoulad je
  varování „zlom v knize? přidej kotvu“. Odhad mimo kotvy se nekontroluje.

## Důsledky

Přidání (minor verze, bez migrace). Kotvy zapsané volně v sezeních zůstávají
platné, do mapy se přepisují ručně. Záznamy se stranou a snímkem slouží jako
kontrolní body, samy se kotvami nestávají.
