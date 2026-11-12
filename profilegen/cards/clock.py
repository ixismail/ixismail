"""When I commit: recent public commits on a 24-hour dial."""
from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

from profilegen.config import LOCAL_OFFSET_LABEL
from profilegen.svg import MONO, SANS
from profilegen.theme import Palette

W, H = 410, 260
CX, CY, INNER, OUTER = 112, 134, 30, 88

# Busiest hour -> label; anything else is a night owl.
KINDS = ((range(5, 9), "early bird"), (range(9, 12), "morning coder"),
         (range(12, 17), "afternoon coder"), (range(17, 21), "evening coder"))
NIGHT = (*range(21, 24), *range(0, 5))


def _point(hour: int, radius: float) -> tuple[float, float]:
    angle = math.radians(hour * 15 - 90)
    return CX + radius * math.cos(angle), CY + radius * math.sin(angle)


def render(times: Sequence[datetime], t: Palette) -> str:
    hours = [0] * 24
    for moment in times:
        hours[moment.hour] += 1
    top = max(hours) or 1
    peak = max(range(24), key=lambda hr: hours[hr])

    bars = []
    for hr, count in enumerate(hours):
        length = INNER + (OUTER - INNER) * count / top if count else INNER + 3
        (x1, y1), (x2, y2) = _point(hr, INNER), _point(hr, length)
        opacity = 1 if hr == peak else (0.5 if count else 0.15)
        bars.append(f'<path d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}" stroke="{t.accent}" stroke-opacity="{opacity}" stroke-width="9" stroke-linecap="round"/>')
    labels = "".join(
        f'<text x="{_point(hr, OUTER + 16)[0]:.1f}" y="{_point(hr, OUTER + 16)[1] + 4:.1f}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{t.muted}">{hr:02d}</text>'
        for hr in (0, 6, 12, 18)
    )
    kind = next((name for hours_range, name in KINDS if peak in hours_range), "night owl")
    share = round(100 * sum(hours[hr] for hr in NIGHT) / (sum(hours) or 1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="When I commit: mostly around {peak:02d}:00, a {kind}; {share}% after 9 pm.">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t.card}" stroke="{t.line}"/>
<circle cx="{CX}" cy="{CY}" r="{OUTER + 4}" fill="none" stroke="{t.line}" stroke-dasharray="2 5"/>
<g>{"".join(bars)}<animateTransform attributeName="transform" type="rotate" values="-20 {CX} {CY};0 {CX} {CY}" dur="1.2s" calcMode="spline" keySplines=".2 0 .2 1" fill="freeze"/></g>
{labels}
<text x="236" y="72" font-family="{MONO}" font-size="11" letter-spacing="2.5" fill="{t.muted}">WHEN I COMMIT</text>
<text x="236" y="112" font-family="{SANS}" font-size="24" font-weight="800" fill="{t.accent}">{peak:02d}:00</text>
<text x="236" y="132" font-family="{MONO}" font-size="11" fill="{t.muted}">busiest hour</text>
<text x="236" y="168" font-family="{SANS}" font-size="16" font-weight="700" fill="{t.text}">{kind}</text>
<text x="236" y="188" font-family="{MONO}" font-size="11" fill="{t.muted}">{share}% after 9 pm</text>
<text x="236" y="226" font-family="{MONO}" font-size="9.5" fill="{t.muted}">{len(times)} public commits · {LOCAL_OFFSET_LABEL}</text>
</svg>
'''
