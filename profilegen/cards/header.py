"""A section header typing `cd ~/<folder>` at a shell prompt."""
from __future__ import annotations

from profilegen.svg import MONO, esc, stepped
from profilegen.theme import Palette

CHAR_W, SIZE = 13.2, 22
TYPE_START, TYPE_STEP = 0.4, 0.07


def render(folder: str, t: Palette) -> str:
    command = f"cd ~/{folder}"
    w = 40 + (2 + len(command)) * CHAR_W + 30
    x_cmd = 20 + 2 * CHAR_W
    text_w = len(command) * CHAR_W
    widths = [CHAR_W * i for i in range(len(command))]
    cursor = [x_cmd + CHAR_W * i for i in range(len(command))]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} 44" width="{w:.0f}" height="44" role="img" aria-label="~/{folder}">
<defs><clipPath id="type"><rect x="{x_cmd - 2}" y="0" height="44" width="{text_w + 4}">{stepped("width", widths, TYPE_START, TYPE_STEP, text_w + 4)}</rect></clipPath></defs>
<text x="20" y="29" font-family="{MONO}" font-size="{SIZE}" font-weight="700" fill="{t.accent}">❯</text>
<text x="{x_cmd}" y="29" clip-path="url(#type)" textLength="{text_w}" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="{SIZE}" font-weight="700" fill="{t.text}">{esc(command)}</text>
<rect x="{x_cmd + text_w + 4}" y="12" width="11" height="22" fill="{t.accent}">{stepped("x", cursor, TYPE_START, TYPE_STEP, x_cmd + text_w + 4)}<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
</svg>
'''
