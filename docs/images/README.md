# Images for the README

## The two kinds of repositories

`proavus-architecture.svg` and `proavus-architecture-dark.svg` (README, ADR
0053) are generated – change `architecture.py` and run
`python3 docs/images/architecture.py`; never edit the SVG by hand. No
sentences in the picture, only names that read the same in every language;
the explanation is in each README below it.

## The family map

Screenshots of `views/mapa.html` built from the **fictional** test family
(`tests/fixtures/family/`). Never use a real family's map here.

Made again when the map changes (macOS, Google Chrome; `$T` is any empty
temporary folder):

1. English copy of the fixture: copy `tests/fixtures/family` to
   `$T/family-en` and add `  lang: en` under `map:` in its `repo.yaml` (the
   fixture's region `cz` makes the map Czech by default).
2. Maps with Karel as the starting person (four generations fit the width):
   `uv run tools/build_views.py tests/fixtures/family --root P-20261020-ab-k01 --out $T/cs.html`
   and the same for `$T/family-en` → `$T/en.html`.
3. Screenshots with headless Chrome, 1120 px wide, scale 1:
   `--headless=new --hide-scrollbars --force-device-scale-factor=1`
   - tree: `--window-size=1120,1036 --screenshot=docs/images/map-tree.<lang>.png file://$T/<lang>.html`
   - detail: `--window-size=1120,980 --virtual-time-budget=2000 --screenshot=docs/images/map-detail.<lang>.png "file://$T/<lang>.html#P-20261020-ab-m01"`
