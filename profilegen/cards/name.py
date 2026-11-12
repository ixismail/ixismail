"""The name typing itself out after the portrait reveal, then the tagline and site link."""
from __future__ import annotations

from profilegen.cards.portrait import REVEAL
from profilegen.config import NAME, SITE, TAGLINE
from profilegen.svg import MONO, SANS, esc, fade_in, stepped
from profilegen.theme import Palette

W, CHAR_W = 560, 22
TYPE_START = REVEAL
TYPE_STEP = 0.1  # seconds per character
TOP = 18  # crops the empty band above the letters


def render(t: Palette) -> str:
    text_w = CHAR_W * len(NAME)
    x0 = (W - text_w) // 2
    widths = [CHAR_W * i for i in range(len(NAME))]
    cursor_x = [x0 + CHAR_W * i for i in range(len(NAME))]
    typed = TYPE_START + TYPE_STEP * len(NAME)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {TOP} {W} {120 - TOP}" width="{W}" height="{120 - TOP}" role="img" aria-label="{esc(NAME)}, {esc(TAGLINE)}. {SITE}">
<defs><clipPath id="typed"><rect x="{x0 - 5}" y="0" height="70" width="{text_w + 10}">{stepped("width", widths, TYPE_START, TYPE_STEP, text_w + 10)}</rect></clipPath></defs>
<text x="{x0}" y="52" clip-path="url(#typed)" textLength="{text_w}" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="34" font-weight="700" fill="{t.accent}">{esc(NAME)}</text>
<rect x="{x0 + text_w + 6}" y="24" width="13" height="34" fill="{t.accent}">{stepped("x", cursor_x, TYPE_START, TYPE_STEP, x0 + text_w + 6)}<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
<text x="{W // 2}" y="86" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="1" fill="{t.tagline}">{esc(TAGLINE)}{fade_in(typed + 0.1)}</text>
<text x="{W // 2}" y="112" text-anchor="middle" font-family="{SANS}" font-size="16" font-weight="500" fill="{t.site}">{SITE} ↗{fade_in(typed + 0.4)}</text>
</svg>
'''
