"""Turn a portrait photo into an animated halftone SVG for the GitHub profile README.

Each grid cell becomes one dot: brighter areas get larger, lighter dots.
Rows fade in from top to bottom while a glowing scan line sweeps down (SMIL,
which GitHub keeps when the SVG is shown through <img>). If a renderer
ignores SMIL, the SVG simply shows the finished portrait.

Usage:  python scripts/halftone.py pic.png assets/portrait-halftone.svg
Needs:  Pillow, numpy
"""
import sys

import numpy as np
from PIL import Image

GRID = 112           # dots per row and column
CELL = 4.0           # SVG units per cell -> 448 x 448 viewBox
REVEAL = 1.82        # seconds for the top-to-bottom sweep (2 s with the last row's fade)
FADE = 0.18          # seconds each row takes to fade in
MIN_LUM = 0.025      # cells darker than this (pure background) get no dot
LIFT = 0.68          # gamma < 1 lifts shadows so dark hair still reads

# dark -> light: ember red to pale gold
RAMP = ["#4a1408", "#8a2a0c", "#c43d0e", "#e8650f", "#f59f1a", "#fcc94a", "#ffe9b0"]


def load_luminance(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGBA")
    # anything transparent counts as black background
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    img = Image.alpha_composite(bg, img).convert("L")
    side = min(img.size)
    img = img.crop(((img.width - side) // 2, (img.height - side) // 2,
                    (img.width + side) // 2, (img.height + side) // 2))
    img = img.resize((GRID, GRID), Image.Resampling.BOX)   # box = average of each cell
    return np.asarray(img, dtype=np.float64) / 255.0


def build_svg(lum: np.ndarray, card: bool = False) -> str:
    """card=True paints a dark rounded background so the dots stay visible on GitHub's light theme."""
    size = GRID * CELL
    rmax = CELL * 0.56
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:.1f} {size:.1f}" '
        f'width="{size:.0f}" height="{size:.0f}" role="img" aria-label="Halftone portrait of Muhammad Ismail">',
        "<style>" + "".join(f".c{i}{{fill:{c}}}" for i, c in enumerate(RAMP)) + "</style>",
        "<defs><linearGradient id=\"scan\" x1=\"0\" x2=\"0\" y1=\"0\" y2=\"1\">"
        "<stop offset=\"0\" stop-color=\"#ffb02e\" stop-opacity=\"0\"/>"
        "<stop offset=\"1\" stop-color=\"#ffe9b0\" stop-opacity=\".9\"/></linearGradient></defs>",
    ]
    if card:
        out.append(f'<rect width="{size:.1f}" height="{size:.1f}" rx="16" fill="#0d1117"/>')
    for row in range(GRID):
        dots = []
        for col in range(GRID):
            if lum[row, col] < MIN_LUM:
                continue
            v = lum[row, col] ** LIFT
            r = rmax * v
            if r < 0.25:
                continue
            shade = min(len(RAMP) - 1, int(v * len(RAMP)))
            cx = (col + 0.5) * CELL
            cy = (row + 0.5) * CELL
            dots.append(f'<circle class="c{shade}" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}"/>')
        if not dots:
            continue
        start = row / GRID * (REVEAL / (REVEAL + FADE))
        end = min(1.0, start + FADE / (REVEAL + FADE))
        out.append(
            f'<g><animate attributeName="opacity" values="0;0;1;1" '
            f'keyTimes="0;{start:.4f};{end:.4f};1" dur="{REVEAL + FADE:.2f}s" fill="freeze"/>'
            + "".join(dots) + "</g>"
        )
    total = REVEAL + FADE
    out.append(
        f'<rect x="0" y="-14" width="{size:.1f}" height="14" fill="url(#scan)" opacity="0">'
        f'<animate attributeName="y" values="-14;{size:.1f}" dur="{REVEAL:.2f}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="0;.8;.8;0" keyTimes="0;.03;.9;1" dur="{total:.2f}s" fill="freeze"/>'
        "</rect>"
    )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "pic.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "assets/portrait-halftone.svg"
    lum = load_luminance(src)
    # transparent version for GitHub dark theme, dark-card version for light theme
    for path, card in ((dst, False), (dst.replace(".svg", "-card.svg"), True)):
        svg = build_svg(lum, card)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {path} ({len(svg) / 1024:.0f} KiB)")
