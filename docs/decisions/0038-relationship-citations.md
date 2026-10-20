# 0038 Přímé citace u vztahu

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Vztah se dal doložit jen přes tvrzení (`assertions`); když zápis vztah uvádí přímo (např. „syn Matěje“), vznikalo umělé tvrzení typu `other` o vztahu.

## Rozhodnutí

`relationship.citations`: stejné citace jako u tvrzení. Prokázaný vztah potřebuje tvrzení **nebo** citace; brána identity platí i pro ně – citovaný zápis musí mít čtení potvrzené člověkem (ADR 0033), účastník citace musí v zápisu existovat.

## Důsledky

Jádro, přidání. Tvrzení o identitě účastníka (ADR 0017) zůstávají samostatná.
