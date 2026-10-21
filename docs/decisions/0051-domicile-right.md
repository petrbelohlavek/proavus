# 0051 Domovská příslušnost u účastníka zápisu (rozšíření `cz` a `at`)

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0015](0015-extensible-schema.md), [ADR 0017](0017-record-participants.md)

## Kontext

V pilotu se domovská příslušnost („příslušný do …“, „zuständig nach …“,
Heimatrecht) objevila v českých i vídeňských zápisech a rozhodla o tom, kde
hledat dál: poručenské spisy nemanželského dítěte vedl okresní soud podle
domovské příslušnosti, i u dítěte narozeného ve Vídni. Zápis ji uvádí
u konkrétní osoby v konkrétní době – je to údaj účastníka, ne osoby.
Dosud se dala zapsat jen do poznámky nebo jako fakt `citizenship`
(odvozený závěr), takže se ztrácelo znění zápisu.

## Rozhodnutí

- U účastníka zápisu (`record#participant`) dvě regionální pole:
  `domicile_as_written` (znění zápisu) a `domicile_place` (místo, výklad –
  odkaz na `places/`). Stejně jako `residence_as_written` /
  `residence_place`.
- Pole jsou ve **vrstvě 3** (ADR 0015), ne v jádře: domovské právo je
  instituce habsburské monarchie a nástupnických států. Definují je
  `cz` i `at` **stejně**; validátor odmítne, kdyby se definice rozešly
  (ADR 0050).
- Závěr o domovském právu osoby zůstává tvrzením (`fact_type`
  `citizenship`) s citací zápisu.
- `method/reading-records.md` §4 a `pitfalls.md` obou regionů říkají, kdy
  pole použít.

## Důsledky

- Test na fiktivní rodině: pole platí s `cz`, s `at` i s oběma, bez
  rozšíření je chyba, `domicile_place` musí odkazovat na existující místo.
- Přidání bez převodu dat (menší verze). Kdyby se pole osvědčilo i mimo
  monarchii, přesune se do jádra novým ADR.
