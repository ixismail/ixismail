""""Thanks For Visiting!" and the "Back to top" button."""
from __future__ import annotations

from profilegen.lettering import thanks
from profilegen.svg import SANS
from profilegen.theme import Palette

THANKS_W, THANKS_H, LETTERING_W = 420, 90, 340
EDGE = 40  # soft edge of the ink mask


def thanks_svg(t: Palette) -> str:
    """A soft-edged mask slides across on a 5.2 s loop: pause, write (2.1 s), hold (1.5 s),
    lift (1 s), pause. It starts and ends hidden, so the restart never shows."""
    w, h = THANKS_W, THANKS_H
    k = LETTERING_W / (thanks.MAX_X - thanks.MIN_X)
    tx = (w - LETTERING_W) / 2 - thanks.MIN_X * k
    ty = (h - (thanks.MAX_Y - thanks.MIN_Y) * k) / 2 + thanks.MAX_Y * k
    span = w + 2 * EDGE
    hidden_before, shown, hidden_after = -span, -EDGE, w
    timeline = (
        f'<animate attributeName="x" values="{hidden_before};{hidden_before};{shown};{shown};{hidden_after};{hidden_after}" '
        'keyTimes="0;.0577;.4615;.75;.9423;1" calcMode="spline" '
        'keySplines="0 0 1 1;.45 0 .25 1;0 0 1 1;.55 0 .75 1;0 0 1 1" dur="5.2s" repeatCount="indefinite"/>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{thanks.TEXT}">
<defs>
<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset="{EDGE / span:.4f}" stop-color="#fff"/><stop offset="{(EDGE + w) / span:.4f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="ink" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}"><rect x="{shown}" y="0" width="{span}" height="{h}" fill="url(#edge)">{timeline}</rect></mask>
</defs>
<g mask="url(#ink)"><path transform="translate({tx:.2f} {ty:.2f}) scale({k:.6f} {-k:.6f})" fill="{t.link}" d="{thanks.PATH}"/></g>
</svg>
'''


def top_svg(t: Palette) -> str:
    w, h, color = 134, 36, t.link
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Back to top">
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{(h - 1) / 2}" fill="{color}" fill-opacity=".06" stroke="{color}" stroke-opacity=".5"/>
<g transform="translate(24 18)"><path d="M0 6V-6M-4.5-1.5L0-6L4.5-1.5" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0;0 0" keyTimes="0;.2;.4;1" dur="2.4s" repeatCount="indefinite"/></path></g>
<text x="40" y="22.5" textLength="76" lengthAdjust="spacingAndGlyphs" font-family="{SANS}" font-size="13" font-weight="600" fill="{color}">Back to top</text>
</svg>
'''
