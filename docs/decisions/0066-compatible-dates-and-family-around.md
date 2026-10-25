# 0066 Slučitelná data různé přesnosti, sourozenci v detailu, rodiče bez partnerství

- **Stav:** přijato (2026-10-25)
- **Původně:** —
- **Upřesňuje:** [ADR 0029](0029-family-map-facts-and-sharing.md), [ADR 0040](0040-validator-advice-and-duplicates.md), [ADR 0063](0063-merging-assertions.md)

## Kontext

Celodenní pátrání v matrikách (Acta Publica, 0.6.2) ukázalo:

- Osoba měla narození podle náhrobku jen rokem a podle matriky dnem. Karta
  v mapě ukázala rok a značku „≠“, i když si obě verze neodporují – mapa
  porovnávala data jako text (to platí i v 0.7, která přidala jen shodu
  ID místa a jména místa).
- Validátor hlásil jen dvě tvrzení se **stejným** datem a
  `merge_assertions.py` (ADR 0063) slučoval jen stejná data; rok a den
  téhož narození zůstaly jako dvě tvrzení.
- U tří párů se zapomněl vztah partnership, ačkoli oba byli rodiči
  společného dítěte.
- Položka `reading.uncertain` obsahující „: “ se v YAML načetla jako
  slovník a hláška „is not of type 'string'“ neřekla, co s tím.
- Sourozence předka a jejich manžele mapa ukazovala jen v seznamu osob mimo
  strom, bez vazby na předka.

## Rozhodnutí

- Dvě data jsou **slučitelná**, když mohou platit obě (rok ⊃ měsíc ⊃ den,
  interval `../datum`, nespecifikované číslice): množiny možných dní se
  protínají (`edtf.compatible`, `edtf.width`). Kvalifikátory `~ ?` datum
  pro tento účel nerozšiřují – odhad 1850~ a 1853~ zůstává rozporem.
- Dvě verze údaje si **odporují** jen při neslučitelném datu, nebo když
  obě uvádějí různé místo či hodnotu (`RepoValidator.facts_agree`; místo
  porovnává `same_place` z 0.7 – chybějící místo neodporuje, ID místa
  a jeho jméno jsou totéž).
- Mapa: z nejsilnější verze a verzí s ní slučitelných ukáže nejpřesnější
  datum; místo, když ho přesnější verze nemá, ze slučitelné verze, která ho
  má. „≠“ jen při skutečném rozporu; ostatní verze v detailu jako „další
  verze“ bez „≠“.
- Validátor varuje u narození/křtu/úmrtí/pohřbu, když méně přesné tvrzení
  souhlasí s přesnějším, a nabídne příkaz `merge_assertions.py plan`;
  ten slučitelná data přijme a ponechá nejpřesnější (s poznámkou v plánu).
- Validátor varuje, když má dítě dva vlastní rodiče (biological,
  legitimated, presumed, bez podtypu) a mezi nimi není partnership. Rodiče,
  kteří spolu nežili v manželství, dostanou nový podtyp slovníku
  `unmarried-parents`; mapa u něj nekreslí znak sňatku.
- Hláška schématu: text, který YAML načetl jako klíč a hodnotu, se hlásí
  s radou dát položku do uvozovek nebo dvojtečku nahradit pomlčkou – pro
  každé textové pole, nejen `reading.uncertain`.
- Detail osoby v mapě má řádek „Sourozenci“: děti vlastních rodičů podle
  narození, polorodí označení, s partnery. Do stromu je nekreslíme –
  strom zůstává stromem předků; přepínač ve stromu odkládáme, dokud se
  neukáže, že detail nestačí.

## Důsledky

- Testy na fiktivní rodině: slučitelná a neslučitelná data, nejpřesnější
  datum na kartě bez „≠“, varování ke sloučení, chybějící partnership a
  `unmarried-parents`, krokový rodič bez varování, hláška u dvojtečky,
  sourozenci a polorodí sourozenci v detailu.
- Nový podtyp je hodnota slovníku (minor), žádná migrace.
