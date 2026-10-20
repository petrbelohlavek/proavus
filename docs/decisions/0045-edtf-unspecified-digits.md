# 0045 EDTF: jednotlivá nespecifikovaná číslice v měsíci a dni

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Zápis bývá čitelný jen zčásti: „1[?]. února“ – 13. nebo 14., nebo „1x. října
až prosince“. Validátor odmítal `1855-02-1X` jako neplatné EDTF; náhradou byl
interval `1855-02-13/1855-02-14`, který ale tvrdí víc, než zápis ukazuje
(nebo méně – „1X“ je 10.–19.).

## Rozhodnutí

Podmnožina EDTF podporuje jednotlivé `X` v **měsíci a dni** známého roku:
`1855-02-1X` (10.–19. 2.), `1855-1X` (říjen–prosinec), `1855-02-X5` (5., 15.
nebo 25. 2.), i s kvalifikátory `?`, `~`, `%` a v intervalech. Podle EDTF jde
o „unspecified digit“ úrovně 2 (úroveň 1 zná jen číslice zprava u roku a celé
`XX`); rozšíření je omezené na měsíc a den.

- `parse()` vrací dál nejširší rozsah let (měsíc a den rok nemění);
- nová `expand()` vrací možné měsíce a dny; datum, kterému neodpovídá žádný
  skutečný den, je neplatné (`1855-02-3X`, `1855-2X`), přestupné roky se
  počítají (`1856-02-2X` končí 29.);
- `XX` v měsíci s konkrétním dnem zůstává neplatné, jako dosud;
- mapa a START-HERE: „10.–19. 2. 1855“, „říjen–prosinec 1855“, „5./15./25. 2.
  1855“; kombinace `X` v měsíci i dni zůstane zapsaná jako EDTF.

## Důsledky

Data platná dosud platí beze změny. Kde se zapsal náhradní interval, lze ho
při dalším čtení zápisu nahradit přesnějším tvarem.
