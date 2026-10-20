# 0040 Validátor: přijatý negativ z rejstříku, pohlaví u identity, duplicity, rady

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Varování „negativ jen z rejstříku“ se opakovalo u každého hledání a nešlo ho
vědomě přijmout. Validátor nehlídal zjevné chyby propojení (otec připojený
k ženě), dvě složky téže osoby ani zdvojená tvrzení. U neznámého stavu života
jen oznámil problém, neporadil.

## Rozhodnutí

- **Negativ z rejstříku:** jedno souhrnné varování se seznamem coverage.
  Badatel může negativ vědomě přijmout polem `index_negative_accepted: {by,
  on, note}` (kdo, kdy a proč rejstřík stačí – např. ověřená úplnost); pak se
  nehlásí. U jiného hledání než negativu z rejstříku je pole varováním.
- **Pohlaví u identity:** pohlaví účastníka (uvedené, jinak odvozené z role:
  otec, ženich, kmotr … / matka, nevěsta, kmotra …) musí odpovídat osobě.
  U pravděpodobné a prokázané identity chyba, u slabší varování.
- **Možné duplicity osob:** stejné jméno (bez diakritiky a velikosti písmen,
  kterákoli podoba) a překrývající se narození → varování u obou. Jmenovce,
  o kterých badatel ví, že jsou dva lidé, označí `person.distinct_from`
  (důvod do těla); jinak sloučení přes `aliases` a bránu identity.
- **Zdvojená tvrzení:** dvě tvrzení stejného typu, data a hodnoty o jedné
  osobě → varování „spojit citace do jednoho tvrzení“. Různá hodnota (dvě
  povolání téhož roku) je v pořádku.
- **Rady u `vital_status: unknown`:** bez dat – doplnit narození nebo křest
  (stačí odhad), úmrtí nebo pohřeb, nebo `deceased`; s narozením v prahu
  žijících – osoba se bere jako žijící, co doplnit, když zemřela nebo žije.

## Důsledky

Nová pole jsou přidání (jádro, ADR 0015). Přijetí negativu i označení
jmenovců jsou rozhodnutí člověka – agent je zapíše jen na jeho slovo.
