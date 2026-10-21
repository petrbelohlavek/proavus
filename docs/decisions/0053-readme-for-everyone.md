# 0053 README pro každého a technická stránka; obrázek bez textu

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Nahrazuje:** popis README v `docs/architecture.md` §2.3 (krátká
  a detailní verze v jednom souboru)

## Kontext

README mělo nahoře pět kroků a pod nimi instalaci pluginu z místní složky,
příkazy `claude plugin …`, kontrolu verze v JSON a tabulku nástrojů. Pro
rodiny bez technických znalostí – hlavní uživatele – bylo po prvních
řádcích nesrozumitelné, a před zveřejněním je to první, co člověk uvidí.
Zvažované varianty: dvě úrovně × dva jazyky (čtyři soubory), jedno README
se sbalovacími sekcemi, lidské README a technika rozdělená do více souborů,
lidské README dvojjazyčně a jedna technická stránka anglicky.

## Rozhodnutí

- **`README.md` (EN) a `README.cs.md` (CS) jsou pro každého:** co Proavus
  udělá, obrázek, co je potřeba, jak začít, připojení člena rodiny,
  soukromí, mapa rodiny. Bez příkazů do terminálu a bez slov jako
  *plugin*, *commit*, *schema* (hlídá test).
- **`TECHNICAL.md` jen anglicky:** dosavadní obsah README – ruční instalace,
  aktualizace, příkazy, nástroje, licence. Kdo instaluje ručně nebo vyvíjí,
  angličtinu přečte, a právě tato část se mění s každým vydáním: překládat
  ji by byla nejdražší údržba. Laik ji nepotřebuje – instalaci za něj dělá
  `/proavus:setup`.
- **Přepínač nahoře** na každé stránce: jazyk (`English · Čeština`)
  a úroveň (`For everyone · Technical`), na dvou řádcích.
- **Obrázek dvou druhů repozitářů** (ADR 0001) bez vět, jen s názvy, které
  se čtou v každém jazyce (`Proavus`, `proavus-novak`): vlevo veřejný
  Proavus pro celý svět, vpravo zamčené domy rodin s rodokmenem, kopie
  Proavus putuje k rodinám, rodokmen nikdy zpět. Vysvětlení je ve větě pod
  obrázkem v jazyce stránky. Obrázek generuje `docs/images/architecture.py`
  (světlá a tmavá verze), test hlídá, že SVG odpovídá generátoru.
- Odkazy „Update to a new release“ a „A family member joins“ vedou do
  `TECHNICAL.md`.

## Důsledky

- Lidské README říká poctivě, že Proavus zatím není dostupný pro každého;
  po zveřejnění (fáze 4) se změní jen tato poznámka a kroky „Jak začít“.
- Písmo nápisů v obrázku (Georgia, neproporcionální písmo) závisí na
  počítači čtenáře; před zveřejněním převést na křivky, stejně jako logo.
- Test (`tests/test_docs.py`): místní odkazy všech tří stránek existují,
  přepínač je všude, lidské README neobsahuje technická slova, obrázek je
  aktuální.
