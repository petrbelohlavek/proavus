# 0058 Svazek zdroje v lokátoru a v coverage

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Doplňuje:** [ADR 0023](0023-citation-locator.md) (citace s povinným lokátorem)

## Kontext

Matriky mají svazky (tomus, Band, svazek, často římskými čísly) a jeden zdroj
může mít svazky, které nejdou po sobě podle let – pozdější svazek obsahuje
dopsané starší zápisy, období se překrývají. Lokátor záznamu pole pro svazek
neměl a validátor `volume` odmítl, takže se svazek psal do `page`. Tím se
strana nedala použít k nalezení snímku ani ke kontrole rozsahu hledání.

## Rozhodnutí

- `common.schema.json`: nová definice `volume` (text nebo číslo, jak stojí
  na knize nebo v portálu).
- `record.locator.volume` a `coverage.ranges[].volume`: volitelné. Svazek
  sám zápis nenajde – lokátor dál potřebuje aspoň jedno z `page`, `folio`,
  `entry`, `image`.
- `source.volumes`: volitelný seznam svazků (`volume`, `period`,
  `call_number`, `url`, `note`) v pořadí archivu, ne nutně podle let.
- Validátor: uvádí-li zdroj `volumes`, musí svazek záznamu i rozsahu coverage
  být jedním z nich (chyba; bez ohledu na velikost písmen) a záznam bez
  svazku dostane varování. Svazek dvakrát v seznamu je chyba. Bez seznamu
  je svazek volný text.
- `family_repo.py upgrade-plan` vypíše záznamy, kde `page` vypadá jako
  svazek (římské číslo, „tom“, „Bd“, „sv.“, „vol.“). Přesouvá se jen se
  souhlasem uživatele, nic se nemění samo.
- Mapa ukazuje svazek v citaci před stranou.

## Důsledky

Přidání do jádra: svazek je obecná součást lokátoru jako folio, ne regionální
údaj (ADR 0015). Minor verze, bez migrace. Svazek jako samostatný `source` se
nezavádí – rozbil by jednu citaci knihy a index, který odkazuje na „knihu,
svazek a stranu“.
