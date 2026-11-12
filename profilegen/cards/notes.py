""""Ask me about" sticky notes."""
from __future__ import annotations

from typing import Any

from profilegen.lettering import notes as lettering
from profilegen.svg import MONO, esc
from profilegen.theme import Palette

# (paper, ink) from the portfolio's components/guestbook/sticky-note.ts.
PAPERS = (("#fff4a3", "#3b3415"), ("#c9f1ff", "#16323d"), ("#ffd6e0", "#43202b"), ("#d9f99d", "#26330f"))
TILTS = (-3, 2, -1.5, 3)
W, H, NOTE = 840, 250, 168
LETTER_PX = 30


def _note(i: int, lines: list[dict[str, Any]], x: float, k: float) -> str:
    paper, ink = PAPERS[i]
    words = "".join(
        f'<path transform="translate({(NOTE - line["advance"] * k) / 2:.1f} {78 + j * 34}) scale({k:.5f} {-k:.5f})" fill="{ink}" d="{line["path"]}"/>'
        for j, line in enumerate(lines)
    )
    return (
        f'<g transform="translate({x + NOTE / 2:.1f} {58 + NOTE / 2}) rotate({TILTS[i]}) translate({-NOTE / 2} {-NOTE / 2})">'
        f'<rect x="3" y="7" width="{NOTE}" height="{NOTE}" fill="#000" opacity=".22" filter="url(#soft)"/>'
        f'<rect width="{NOTE}" height="{NOTE}" fill="{paper}"/>'
        f'<rect x="{NOTE / 2 - 30}" y="-9" width="60" height="18" fill="#fff" opacity=".55" transform="rotate({-TILTS[i] * 1.5} {NOTE / 2} 0)"/>'
        f"{words}</g>"
    )


def render(t: Palette) -> str:
    k = LETTER_PX / lettering.UNITS_PER_EM
    gap = (W - 4 * NOTE) / 5
    notes = "".join(_note(i, lines, gap + i * (NOTE + gap), k) for i, lines in enumerate(lettering.NOTES))
    topics = "; ".join(" ".join(line["text"] for line in lines) for lines in lettering.NOTES)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Ask me about: {esc(topics)}.">
<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter></defs>
<text x="{W / 2}" y="22" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{t.muted}">ASK ME ABOUT</text>
{notes}
</svg>
'''
