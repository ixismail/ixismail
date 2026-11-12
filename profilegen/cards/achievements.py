"""Bucket-list goals as rubber stamps."""
from __future__ import annotations

from profilegen.svg import MONO, esc
from profilegen.theme import Palette

# Done goals from the portfolio's content/bucket-list/goals.ts: (line 1, line 2, footer).
ACHIEVEMENTS = (
    ("PORTFOLIO", "SHIPPED", "MAR 2025"),
    ("INTERNSHIP", "LANDED", "MAY 2024"),
    ("MENTORED A", "JUNIOR DEV", "DONE"),
    ("2 SELF-HELP", "BOOKS READ", "DONE"),
    ("NEVER VAPED", "OR SMOKED", "20 YEARS"),
)
TILTS = (-6, 4, -3, 5, -4)
W, H = 840, 196


def _stamp(i: int, line1: str, line2: str, foot: str, cx: float, t: Palette) -> str:
    color = t.ember if i % 2 else t.accent
    delay = 0.25 + i * 0.22
    dur = delay + 0.25
    press = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{delay / dur:.3f};1" dur="{dur:.2f}s" fill="freeze"/>'
             f'<animateTransform attributeName="transform" type="scale" additive="sum" values="1.25;1.25;1" keyTimes="0;{delay / dur:.3f};1" dur="{dur:.2f}s" fill="freeze"/>')
    return (
        f'<g transform="translate({cx:.1f} 112) rotate({TILTS[i]})"><g opacity=".9">{press}'
        f'<circle r="62" fill="none" stroke="{color}" stroke-width="3"/>'
        f'<circle r="55" fill="none" stroke="{color}" stroke-width="1.2" stroke-dasharray="3 3"/>'
        f'<text y="-6" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" letter-spacing="1" fill="{color}">{esc(line1)}</text>'
        f'<text y="12" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" letter-spacing="1" fill="{color}">{esc(line2)}</text>'
        f'<path d="M-30 22H30" stroke="{color}" stroke-width="1"/>'
        f'<text y="38" text-anchor="middle" font-family="{MONO}" font-size="9.5" letter-spacing="2" fill="{color}">{esc(foot)}</text>'
        "</g></g>"
    )


def render(t: Palette) -> str:
    pitch = (W - 48) / len(ACHIEVEMENTS)
    stamps = "".join(_stamp(i, *goal, 24 + pitch * (i + 0.5), t) for i, goal in enumerate(ACHIEVEMENTS))
    label = "; ".join(f"{a} {b} ({c.lower()})" for a, b, c in ACHIEVEMENTS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Achievements unlocked: {esc(label)}.">
<text x="{W / 2}" y="22" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{t.muted}">ACHIEVEMENTS UNLOCKED · FROM MY BUCKET LIST</text>
{stamps}
</svg>
'''
