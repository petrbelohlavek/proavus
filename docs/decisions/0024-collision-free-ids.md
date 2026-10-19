# 0024 ID bez kolizí

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Více lidí na více počítačích zakládá soubory souběžně; pořadová čísla by kolidovala.

## Rozhodnutí

ID `<PREFIX>-<YYYYMMDD>-<zkratka člena>-<3 znaky>`, např. `Q-20261019-jn-k7m`. Prefixy: Q, S, C, R, SO, P, RL, A, X, PL, O, D, CH. Znaky bez záměnných (0/o, 1/l/i). `new_id.py` ověří, že ID ještě neexistuje. Název souboru `<ID>.md` nebo `<ID>--<slug>.md`. Při sloučení dvou osob zůstává jedno ID, druhé je alias (`aliases`) a odkazy na něj dál platí.

## Důsledky

Zkratky členů jsou v `repo.yaml`; validátor odmítne neznámou zkratku a duplicitní ID.
