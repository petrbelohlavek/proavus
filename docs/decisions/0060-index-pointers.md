# 0060 Index jako ukazatel: `coverage.pointers`

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Doplňuje:** [ADR 0035](0035-coverage-query.md) (hledání v databázi),
  navazuje na metodu z 0.6.1 (index a kniha jsou dvě hledání)

## Kontext

Index (rejstřík, samostatná indexová kniha, online index) odkazuje na jinou
knihu, svazek a stranu, ale sám zápis neobsahuje. Odkaz se dosud psal jen
do poznámky coverage, takže ho nástroje neznaly: nešlo zjistit, které stopy
z indexu ještě nikdo nedohledal v knize, ani zkontrolovat, že hledání
v knize pokrylo stranu, na kterou index ukazuje. Jediné selhání v evalech
(`index-is-not-the-record`) bylo právě vzít údaj z indexu za zápis.

## Rozhodnutí

- Coverage indexu (`method: index`) má volitelné `pointers`: jméno, jak ho
  index uvádí (`name_as_written`), volitelně `event` a `date_as_written`,
  cíl `to: {source, volume, page, folio, entry, image}` (kniha a aspoň jedno
  místo v ní), `followed` (coverage hledání v té knize) a `note`.
- Ukazatel je stopa, ne tvrzení: nemá účastníky ani osobu, z ukazatele
  nevznikne `record` ani tvrzení o identitě. Zamítnutá varianta: `record`
  s událostí „index-entry“ – vypadá jako zápis a svádí k propojení s osobou.
- Validátor: ukazatele jen u `method: index` a s výsledkem `found` nebo
  `partial` (pak `found` není potřeba); cíl nesmí být index sám; svazek cíle
  musí být mezi `source.volumes`; `followed` musí hledat v knize, kam
  ukazatel vede (chyba), a pokud jeho rozsahy nepokrývají svazek nebo stranu
  cíle, varování. Tvrzení, které cituje hledání v indexu jinak než jako
  negativní důkaz, dostane varování.
- START-HERE vypíše ukazatele, které ještě nikdo nedohledal v knize.

## Důsledky

Přidání (minor verze, bez migrace); starší coverage s ukazatelem v poznámce
zůstává platná. Když index sám nese údaje, které chceme citovat, jde to dál
přes `record` z odvozeného zdroje (`form: derivative`) – výjimka, ne cesta
pro odkazy.
