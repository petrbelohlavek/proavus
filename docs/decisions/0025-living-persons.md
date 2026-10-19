# 0025 Žijící osoby

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Historie gitu nic nezapomene; o žijících se má ukládat jen nezbytné minimum.

## Rozhodnutí

`person.vital_status`: deceased / living / unknown. Osoba bez údaje o úmrtí narozená před méně než `living_threshold_years` (výchozí 110) je považována za žijící. U žijících se smí ukládat jen jméno, pohlaví, narození a vztahy; u žijících nezletilých (méně než 18 let) ani datum narození. Kontroluje validátor (a v rodinném repu hook před uložením). Souhlasy se zapisují do `decisions/`.

## Důsledky

Obsah konkrétních pravidel rodiny (kdo souhlasil) je rozhodnutí rodiny. DNA je mimo rozsah.
