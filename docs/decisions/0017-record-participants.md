# 0017 Účastníci zápisu jsou oddělení od osob

- **Stav:** přijato (2026-10-20)
- **Původně:** R22

## Kontext

Zápis uvádí lidi tak, jak je zapsal farář; ztotožnění se skutečnou osobou je úsudek, který se může mýlit (jmenovci).

## Rozhodnutí

`record` obsahuje **účastníky** přesně podle zápisu (jméno v zapsané podobě, role, věk, bydliště, povolání, vyznání). Účastník není osoba ve stromu. Propojení „účastník X zápisu Y = osoba P“ je samostatné tvrzení `kind: identity` s jistotou a podléhá bráně identity. Role účastníků jsou slovník a pokrývají FAN (kmotři, svědci, sousedé) bez zvláštní entity.

## Důsledky

Chybné ztotožnění jde opravit bez zásahu do přepisu. Kmotři a svědci jsou zapsaní vždy, nejen rodina.
