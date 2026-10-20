# 0029 Mapa rodiny: data slovy, výběr údaje, žijící a sdílení

- **Stav:** přijato (2026-10-20)
- **Původně:** —
- **Doplňuje:** [ADR 0027](0027-family-map.md), [ADR 0028](0028-family-map-layout.md)

## Kontext

Mapa ukazovala data ve tvaru EDTF (`1850~`, `../1836-01-26`), u osoby s více
údaji téhož druhu brala první podle jistoty a v rámečcích rozporů a otázek
ukazovala ID. Rodina mapu čte, ne zdrojové soubory; a chce ji někdy ukázat
i lidem mimo rodinu.

## Rozhodnutí

- **Data slovy v jazyce mapy:** cs `13. 5. 1958`, `kolem 1868`, `1904?`,
  `před 26. 1. 1836`, `po 1900`, `1946/1947`, `duben 1935`, `1930–1939`; en
  obdobně (`13 May 1958`, `about 1868`, `before …`). Štítek sňatku krátce
  (`~1877`, `1877?`, `<1836`).
- **Jazyk mapy** je `map.lang`; když chybí, podle prvního regionu repa, pro
  který je jazyk (`cz` → `cs`), jinak `en`.
- **Více údajů téhož druhu** (např. dvě narození): na kartu jde nejsilnější
  podle nejlepší citace – *information* (primary > secondary > undetermined),
  pak *evidence* (direct > indirect > negative), pak *confidence* (ADR 0022).
  Ostatní jsou v detailu („jiná verze“). Liší-li se jiná verze v datu, místě
  nebo hodnotě, má karta značku **≠**: „stejně silná jiná verze“, je-li stejně
  silná, jinak „jiná verze se liší“. Stejný údaj z dalšího zdroje značku nemá.
  U žijících nezletilých se nic z toho neukazuje.
- **Jména místo ID:** odkazy ukazují jméno osoby, název zápisu (událost,
  datum, místo, hlavní osoba jak je zapsaná), zdroje, otázky, „Rozpor“ apod.;
  ID je jen cíl odkazu a bublina.
- **Dlouhá povolání a místa** se na kartě zkracují (32 a 30 znaků, „…“), plný
  text je v bublině a v detailu.
- **Místo narození žijících** jen s `map.living_places: true` (výchozí
  `false`). Pravidlo 9 narození dovoluje; zda se ukáže i místo, rozhoduje
  rodina. Když je vypnuté, nezobrazí se u žijících ani název zdroje a
  poznámka citace – název matriky farnost prozradí.
- **Verze pro sdílení mimo rodinu:** `build_views.py --hide-living` zapíše
  `views/mapa-sdileni.html` (rodinnou mapu nepřepíše): žijící bez jmen, dat,
  míst a údajů („Žijící osoba“), jen vazby stromu; bez boxu „Další kroky“
  (volný text sezení může jmenovat kohokoli).

## Důsledky

Výběr údaje je mechanický a vysvětlitelný; o tom, která verze je pravdivá,
dál rozhoduje badatel v `conflicts/` (značka ≠ k tomu vede). Verze pro
sdílení nečte volné texty – co by v nich mohlo být o žijících, do ní nejde.
