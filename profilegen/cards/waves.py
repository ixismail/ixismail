"""The top and bottom wave banners: a fixed gradient seen through two rolling wave masks."""
from __future__ import annotations

import math
from dataclasses import dataclass

W, H = 1200, 120
GREEN, BLUE = "#5fb06f", "#0a87ba"
TOP_CROP = 92  # the top banner never reaches below y 88


@dataclass(frozen=True)
class Layer:
    mid: float
    amplitude: float
    phase: float  # in wave-lengths
    seconds: float  # per wave-length
    opacity: float
    direction: int  # 1 right, -1 left


LAYERS = (
    Layer(54, 22, 0.0, 16, 0.5, 1),    # back
    Layer(82, 13, 0.5, 10, 0.92, -1),  # front
)


def wave_path(layer: Layer) -> str:
    """Two wave-lengths, placed on the side the layer rolls in from so the banner stays covered;
    it moves one wave-length per loop, so the loop is seamless."""
    start = -W if layer.direction > 0 else 0
    points = [
        f"{x} {layer.mid + layer.amplitude * math.sin(2 * math.pi * (x / W + layer.phase)):.1f}"
        for x in range(start, start + 2 * W + 1, 25)
    ]
    return f"M{points[0]}L{'L'.join(points[1:])}V{H}H{start}Z"


def render(edge: str) -> str:
    """`top` is `bottom` mirrored."""
    flip = f' transform="translate(0 {H}) scale(1 -1)"' if edge == "top" else ""
    h = TOP_CROP if edge == "top" else H
    masks, layers = [], []
    for i, layer in enumerate(LAYERS):
        masks.append(
            f'<mask id="wave{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<path fill="#fff" d="{wave_path(layer)}">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{W * layer.direction} 0" '
            f'dur="{layer.seconds}s" repeatCount="indefinite"/></path></mask>'
        )
        layers.append(f'<rect width="{W}" height="{H}" fill="url(#sea)" mask="url(#wave{i})" opacity="{layer.opacity}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" preserveAspectRatio="none" role="img" aria-label="">
<defs>
<linearGradient id="sea" x1="0" x2="1"><stop offset="0" stop-color="{GREEN}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>
{"".join(masks)}
</defs>
<g{flip}>{"".join(layers)}</g>
</svg>
'''
