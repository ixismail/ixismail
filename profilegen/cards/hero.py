"""A still of the homepage's three.js desk."""
from __future__ import annotations

from profilegen.config import ART, SITE
from profilegen.svg import MONO, SANS, data_uri
from profilegen.theme import Palette

W, H = 410, 260


def render(t: Palette) -> str:
    image = data_uri(ART / "hero-computer.webp", "image/webp")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="The 3D desk from my homepage, rendered live in three.js on {SITE}">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t.card}" stroke="{t.line}"/>
<text x="20" y="30" font-family="{MONO}" font-size="11" letter-spacing="2.5" fill="{t.muted}">ON MY HOMEPAGE</text>
<image href="{image}" x="25" y="52" width="360" height="135"/>
<text x="20" y="222" font-family="{SANS}" font-size="15" font-weight="600" fill="{t.text}">A desk you can turn around</text>
<text x="20" y="242" font-family="{SANS}" font-size="12.5" fill="{t.muted}">Rendered live with three.js · <tspan fill="{t.link}">{SITE} ↗</tspan></text>
</svg>
'''
