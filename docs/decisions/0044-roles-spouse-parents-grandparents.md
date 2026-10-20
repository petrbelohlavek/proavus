# 0044 Role účastníků: rodiče manžela/manželky, děd a babička bez strany

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Při bráně identity v jednom rodinném repu (20. 10. 2026) se ukázaly dvě
role, které slovník `participant_roles` neuměl, a musely se zapsat jako
`other` s poznámkou:

- úmrtní zápis uvádí u zemřelého manželku a jejího otce (fiktivně:
  „manžel Marie, rozené Vzorové, dcery Jana Vzora z č. 10“) – Jan je otec
  manželky hlavní osoby;
- sňatek nemanželského ženicha uvádí jeho děda z matčiny strany – role
  `paternal-` / `maternal-grandfather` jsou vztažené k hlavní osobě a strana
  ani „čí“ nesedí.

## Rozhodnutí

Do slovníku (vrstva 2, ADR 0015) přibývá:

- `spouse-father`, `spouse-mother` – otec a matka manžela/manželky hlavní
  osoby;
- `grandfather`, `grandmother` – děd a babička, u nichž strana nebo čí jsou
  neuvedeny; čí to je, patří do `note`. Místo obecného `grandparent` dvě
  hodnoty, protože pohlaví z role využívá kontrola pohlaví u identity
  (ADR 0040) – role tyto čtyři hodnoty zná.

## Důsledky

Přidání hodnot = menší verze bez převodu dat. Staré zápisy s `other` zůstávají
platné; přepsat je lze při dalším čtení zápisu.
