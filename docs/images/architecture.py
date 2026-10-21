#!/usr/bin/env python3
"""The README picture of the two kinds of repositories (ADR 0053): public Proavus, private family repositories.

No sentences in the picture – only names that read the same in every
language – so one picture serves every README. Writes
proavus-architecture.svg and proavus-architecture-dark.svg next to this file:

    python3 docs/images/architecture.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

THEMES = {
    "light": dict(ink="#1F3A5F", sepia="#B8742A", panel="#F6F1E7", paper="#FFFFFF", onink="#FFFFFF", red="#B23A3A", muted="#7A8798"),
    "dark":  dict(ink="#F6F1E7", sepia="#D08A3C", panel="#14263D", paper="#1F3A5F", onink="#14263D", red="#E06464", muted="#AFC0D6"),
}
SERIF = "font-family=\"Georgia, 'Times New Roman', serif\""
MONO = "font-family=\"'SFMono-Regular', Menlo, Consolas, 'DejaVu Sans Mono', monospace\""


def person(x, y, s, fill):
    return (f'<circle cx="{x}" cy="{y}" r="{7 * s:.1f}" fill="{fill}"/>'
            f'<path d="M{x - 11 * s:.1f} {y + 24 * s:.1f} Q{x - 11 * s:.1f} {y + 9 * s:.1f} {x} {y + 9 * s:.1f} '
            f'Q{x + 11 * s:.1f} {y + 9 * s:.1f} {x + 11 * s:.1f} {y + 24 * s:.1f} Z" fill="{fill}"/>')


def mark(x, y, s, t, paper=None):
    """The Proavus mark (brand/proavus-mark.svg), top-left corner of its 512 box at x, y."""
    paper = paper or t["paper"]
    return f'''<g transform="translate({x} {y}) scale({s})">
<path d="M64 400 L64 150 Q160 118 250 150 L250 400 Q160 370 64 400 Z" fill="{paper}" stroke="{t["ink"]}" stroke-width="14" stroke-linejoin="round"/>
<path d="M262 150 Q352 118 448 150 L448 400 Q352 370 262 400 Z" fill="{paper}" stroke="{t["ink"]}" stroke-width="14" stroke-linejoin="round"/>
<g stroke="{t["sepia"]}" stroke-width="10" stroke-linecap="round"><line x1="100" y1="205" x2="216" y2="205"/><line x1="100" y1="245" x2="216" y2="245"/><line x1="100" y1="285" x2="188" y2="285"/><line x1="100" y1="325" x2="216" y2="325"/></g>
<path d="M300 275 L338 275 M338 212 L338 338 M338 212 L392 212 M338 338 L392 338" fill="none" stroke="{t["ink"]}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="296" cy="275" r="15" fill="{t["ink"]}"/><circle cx="406" cy="212" r="15" fill="{t["ink"]}"/><circle cx="406" cy="338" r="15" fill="{t["sepia"]}"/></g>'''


def badge(cx, cy, t, r=24):
    """A small round Proavus badge: the copy every family gets."""
    s = (2 * r * 0.78) / 384
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t["paper"]}" stroke="{t["sepia"]}" stroke-width="3.5"/>'
            + mark(cx - 256 * s, cy - 268 * s, s, t))


def padlock(x, y, t, s=1.0):
    return (f'<rect x="{x - 13 * s}" y="{y}" width="{26 * s}" height="{21 * s}" rx="{4 * s}" fill="{t["ink"]}"/>'
            f'<path d="M{x - 8 * s} {y} L{x - 8 * s} {y - 6 * s} Q{x - 8 * s} {y - 15 * s} {x} {y - 15 * s} '
            f'Q{x + 8 * s} {y - 15 * s} {x + 8 * s} {y - 6 * s} L{x + 8 * s} {y}" fill="none" stroke="{t["ink"]}" stroke-width="{3.5 * s}"/>'
            f'<circle cx="{x}" cy="{y + 10 * s}" r="{2.6 * s}" fill="{t["onink"]}"/>')


def pedigree(cx, top, t, s=1.0, card=False):
    """A family tree everyone recognises: four grandparents, two parents, one child."""
    gx = [cx - 45 * s, cx - 15 * s, cx + 15 * s, cx + 45 * s]
    px = [cx - 30 * s, cx + 30 * s]
    y0, y1, y2 = top, top + 30 * s, top + 60 * s
    out = f'<g fill="none" stroke="{t["ink"]}" stroke-width="{2.6 * s:.1f}" stroke-linecap="round">'
    for i, p in enumerate(px):
        a, b = gx[2 * i], gx[2 * i + 1]
        out += f'<path d="M{a} {y0} L{a} {y0 + 14 * s} L{b} {y0 + 14 * s} L{b} {y0} M{p} {y0 + 14 * s} L{p} {y1}"/>'
    out += f'<path d="M{px[0]} {y1} L{px[0]} {y1 + 14 * s} L{px[1]} {y1 + 14 * s} L{px[1]} {y1} M{cx} {y1 + 14 * s} L{cx} {y2}"/></g>'
    for x in gx:
        out += f'<circle cx="{x}" cy="{y0}" r="{6.5 * s:.1f}" fill="{t["ink"]}"/>'
    for x in px:
        out += f'<circle cx="{x}" cy="{y1}" r="{6.5 * s:.1f}" fill="{t["ink"]}"/>'
    out += f'<circle cx="{cx}" cy="{y2}" r="{7.5 * s:.1f}" fill="{t["sepia"]}"/>'
    if card:
        out = (f'<rect x="{cx - 62 * s}" y="{top - 16 * s}" width="{124 * s}" height="{92 * s}" rx="{8 * s}" fill="{t["paper"]}" stroke="{t["ink"]}" stroke-width="{2.5 * s}"/>' + out)
    return out


def house(x, y, name, people, t):
    w = 210
    out = f'''<path d="M{x - 8} {y + 52} L{x + w / 2} {y} L{x + w + 8} {y + 52} Z" fill="{t["paper"]}" stroke="{t["ink"]}" stroke-width="5" stroke-linejoin="round"/>
<rect x="{x}" y="{y + 50}" width="{w}" height="112" fill="{t["paper"]}" stroke="{t["ink"]}" stroke-width="5" stroke-linejoin="round"/>
{padlock(x + w / 2, y + 26, t, 0.85)}
{pedigree(x + 78, y + 74, t, 0.95)}
{badge(x + 170, y + 130, t, 25)}
<text x="{x + w / 2}" y="{y + 190}" text-anchor="middle" font-size="19" fill="{t["ink"]}" {MONO}>{name}</text>'''
    for i in range(people):
        out += person(x + w + 30 + i * 27, y + 100, 1.0, t["ink"])
    return out


def svg(t):
    W, H = 1200, 800
    top, height = 20, 700                       # both panels: the same top and height
    mid = top + height / 2
    houses = [(720, 46, "proavus-novak", 3), (720, 272, "proavus-smith", 2), (720, 498, "proavus-muller", 4)]
    b = ""
    # left: Proavus – one for everyone, open to the world
    b += f'<rect x="20" y="{top}" width="420" height="{height}" rx="28" fill="{t["panel"]}"/>'
    b += mark(100, 92, 0.52, t)
    b += f'<text x="230" y="362" text-anchor="middle" font-size="54" fill="{t["ink"]}" {SERIF}>Proavus</text>'
    # the world: a globe surrounded by many people
    gx, gy, r = 230, 520, 46
    b += (f'<g fill="none" stroke="{t["ink"]}" stroke-width="4"><circle cx="{gx}" cy="{gy}" r="{r}"/>'
          f'<ellipse cx="{gx}" cy="{gy}" rx="{r * 0.45}" ry="{r}"/><path d="M{gx - r} {gy} L{gx + r} {gy}"/>'
          f'<path d="M{gx - r * 0.87} {gy - r * 0.5} Q{gx} {gy - r * 0.3} {gx + r * 0.87} {gy - r * 0.5}"/>'
          f'<path d="M{gx - r * 0.87} {gy + r * 0.5} Q{gx} {gy + r * 0.3} {gx + r * 0.87} {gy + r * 0.5}"/></g>')
    for x, y in ((90, 490), (120, 540), (90, 590), (370, 490), (340, 540), (370, 590), (180, 600), (280, 600)):
        b += person(x, y, 1.0, t["ink"])
    # right: the private world of the families
    b += f'<rect x="680" y="{top}" width="440" height="{height}" rx="28" fill="{t["panel"]}"/>'
    # one Proavus for every family: each arrow carries a copy (the badge)
    for hx, hy, _, _ in houses:
        ty = hy + 106
        b += f'<path d="M444 {mid} C540 {mid} 520 {ty} {hx - 150} {ty} L{hx - 22} {ty}" fill="none" stroke="{t["sepia"]}" stroke-width="5" stroke-linecap="round"/>'
        b += f'<path d="M{hx - 34} {ty - 10} L{hx - 20} {ty} L{hx - 34} {ty + 10}" fill="none" stroke="{t["sepia"]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        b += badge(hx - 88, ty, t, 28)
    # never back: a family tree stopped on its way to the public side
    y = top + height + 45
    b += f'''<path d="M900 {top + height} L900 {y} L230 {y} L230 {top + height + 4}" fill="none" stroke="{t["red"]}" stroke-width="5" stroke-dasharray="10 9" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M220 {top + height + 20} L230 {top + height + 4} L240 {top + height + 20}" fill="none" stroke="{t["red"]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
{pedigree(680, y - 23, t, 0.55, card=True)}
<circle cx="450" cy="{y}" r="26" fill="{t["paper"]}" stroke="{t["red"]}" stroke-width="5"/>
<path d="M432 {y + 18} L468 {y - 18}" stroke="{t["red"]}" stroke-width="5" stroke-linecap="round"/>'''
    for hx, hy, name, n in houses:
        b += house(hx, hy, name, n, t)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Proavus is one, open to the whole world. Every family gets its own copy of Proavus in a private, locked repository such as proavus-novak, with its family tree inside. A family tree never goes back to the public side.">
<title>Proavus and the family repositories</title>
{b}
</svg>
'''


for name, t in THEMES.items():
    (HERE / f"proavus-architecture{'-dark' if name == 'dark' else ''}.svg").write_text(svg(t), encoding="utf-8")
