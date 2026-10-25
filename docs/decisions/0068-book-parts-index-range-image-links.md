# 0068 Části knihy a skutečný rozsah rejstříku; odkazy na snímky Acta Publica

- **Stav:** přijato (2026-10-25)
- **Původně:** —
- **Upřesňuje:** [ADR 0040](0040-validator-advice-and-duplicates.md), [ADR 0041](0041-archive-portals.md), [ADR 0058](0058-source-volumes.md), [ADR 0061](0061-page-image-anchors.md)

## Kontext

Pátrání v Acta Publica (MZA) s verzí 0.6.2 ukázalo (svazky, mapu strana →
snímek a ukazatele rejstříku mezitím přinesla 0.7, ADR 0058, 0060, 0061;
zbývá to, co tam není):

- Knihy mají části (obce, oddíly) a hledá se po nich. Coverage neměla, kam
  část zapsat, a u části bez známého prvního snímku („do snímku N“) se
  rozsah obcházel přes `note`.
- Rejstřík pokrýval jiný rozsah, než uvádějí metadata archivu: kniha podle
  metadat zahrnuje celé období, oddíl písmene v rejstříku ale začíná
  o desítky let později. Negativ z takového rejstříku o dřívějších letech
  nic neříká – a varování „negative from index only“ to nevědělo.
- Adresa snímku v prohlížeči Acta Publica má tvar
  `…/matrika/detail/<id>?image=<prefix>-<číslo snímku × 10, pět číslic>.jp2`;
  `archive_fetch.py link` uměl jen starší tvar s `signatura` a `strana`.
- Posun strana → snímek se liší po **částech** knihy, které mají vlastní
  stránkování; `source.image_map` (ADR 0061) má mapu na svazek, ne na část.
- Plné křestní jméno z matriky (dvě křestní jména) nemělo typ jména.
- Zápis 20–30 souborů znamenal 20–30 spuštění `new_id.py`.

## Rozhodnutí

- `coverage.ranges[].part` (volitelné): část knihy, jak ji jmenuje kniha
  nebo portál – obec, oddíl, písmeno rejstříku. `pages` smí začínat `..`
  (`..-250`, `images ..-250`), když první strana či snímek části nejsou
  známé.
- `coverage.index_covers` (volitelné, EDTF, jen s `method: index`):
  období, které rejstřík ověřeně pokrývá. Validátor varuje, když hledaná
  data sahají mimo něj – i u negativu přijatého přes
  `index_negative_accepted`, protože léta mimo rejstřík nikdo neprošel.
- `archive_fetch.py link` přijme adresu snímku z prohlížeče
  (`…/matrika/detail/<id>?image=…jp2`) a složí adresu snímku N; starší
  tvar se `signatura` zůstává. Nic se nestahuje (přístup `link`).
- Slovník `name_types`: `baptismal` – plné křestní jméno se všemi jmény
  z matriky.
- `new_id.py --count N`: N různých ID jedním spuštěním (nejvýš 200),
  navzájem i proti repozitáři bez kolize.
- `source.image_map[].part` (volitelné): mapa pro část knihy s vlastním
  stránkováním – jedna mapa na svazek a část. `locate.py --part P` ji
  použije; bez `--part` se použije jen mapa bez části a mapa jiné části
  se nikdy nepoužije (raději „mapa chybí“ než špatný snímek).

## Důsledky

- Testy: část a otevřený začátek rozsahu, mapa snímků po částech (výpočet,
  dvě mapy jedné části, `locate.py --part`), `index_covers` užší i stejný jako
  hledaný rozsah, u přijatého negativu, mimo rejstřík; odkaz na snímek
  z adresy prohlížeče a chybějící `image=`; `new_id.py --count`.
- Vše volitelné – starší coverage platí, migrace není potřeba.
