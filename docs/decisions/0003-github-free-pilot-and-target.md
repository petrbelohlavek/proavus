# 0003 GitHub zdarma: pilot na osobním účtu, cílově organizace s modelem forků

- **Stav:** přijato (2026-10-20)
- **Původně:** R3, R4, R13

## Kontext

Hosting má být pro rodinu zdarma. GitHub Free u soukromých rep nevynutí ochranu větve ani CODEOWNERS.

## Rozhodnutí

**Pilot:** soukromé repo na osobním účtu správce, 2–3 důvěryhodní spolupracovníci se zápisem, kontrola dohodou a bránou identity (ADR 0016). **Cílový stav:** organizace rodiny, schvalovatelé se zápisem, badatelé jen čtení + soukromý fork a návrhy změn; dva vlastníci kvůli kontinuitě.

## Důsledky

Pilot nepotřebuje složité mechanismy. Přechod do organizace (převod repa) zachová historii i odkazy; kritéria přechodu jsou v architektuře (kap. 4).
