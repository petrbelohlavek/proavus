# 0067 Stopy: zápisy s nedoloženou vazbou na rodinu v otázce

- **Stav:** přijato (2026-10-25)
- **Původně:** —
- **Upřesňuje:** [ADR 0039](0039-start-here-readable.md), [ADR 0060](0060-index-pointers.md)

## Kontext

Při procházení matrik se najdou zápisy, které **mohou** patřit k rodině
(stejné číslo domu, jméno, kmotr), ale vazba doložená není. Zapsat je jako
record a tvrzení by předbíhalo důkaz a do dat by se dostali cizí lidé;
zahodit je znamená hledat je příště znovu. V pilotu skončily jako volný
text v těle otázky – START-HERE o nich nevěděl a nedalo se poznat, které
jsou vyřízené.

## Rozhodnutí

- Otázka má volitelné pole `leads`: seznam stop, každá s `where` (kniha
  a pozice, jak je jmenuje portál – část, snímek, zápis), volitelně
  `source` a `url`, `why` (proč je podezřelá), `by`, `on` a `status`
  `open` / `confirmed` / `rejected`.
- Stopa **nenese jména cizích osob** – jen kde je a proč; přepis patří až
  do recordu po potvrzení. Stroj to zkontrolovat neumí, říká to popis pole
  a metodika.
- Uzavření: `confirmed` potřebuje `record` (zápis přepsaný podle metodiky)
  a `closed: {by, on}`; `rejected` potřebuje `closed: {by, on, note}`
  s důvodem. Stopa se nemaže – zamítnutá stopa je informace pro příště.
- Stopa není ukazatel rejstříku (`coverage.pointers`, ADR 0060): ukazatel
  je to, co rejstřík dal pro hledané jméno, a vede do knihy; stopa je zápis
  nalezený přímo v knize, u něhož chybí důkaz vazby na rodinu.
- Pole je v otázce, ne nová entita: stopa vždy vzniká při práci na otázce
  a bez ní nemá smysl; vlastní soubor by přidal ID a odkazy bez užitku.
- START-HERE vypisuje otevřené stopy pod jejich otázkou; validátor varuje,
  když uzavřená otázka (answered, bounded, abandoned) má otevřené stopy.

## Důsledky

- Testy na fiktivní rodině: otevřená stopa, potvrzení bez recordu,
  zamítnutí bez důvodu, otevřená stopa v uzavřené otázce, výpis ve
  START-HERE.
- Volitelné pole – starší otázky platí, migrace není potřeba. Stopy z těla
  otázek může člen přepsat do `leads` sám; automaticky to nejde.
