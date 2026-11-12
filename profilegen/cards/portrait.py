"""The halftone portrait, revealed top to bottom with a scan line.

Thousands of tiny vector dots render blotchy at 1x, so the dots are embedded as a 3x raster:
  1. `python -m profilegen portrait-dots` draws art/portrait-dots.svg from art/portrait.pgm.
  2. Rasterise it to art/portrait-halftone.webp, e.g. with sharp:
     sharp(dots, { density: 72 * 672 / 448 }).webp({ lossless: true }).
  3. `python -m profilegen static` wraps the raster into the README's SVGs.
"""
from __future__ import annotations

from profilegen.config import ART, NAME
from profilegen.svg import data_uri

SOURCE = ART / "portrait.pgm"
DOTS = ART / "portrait-dots.svg"
RASTER = ART / "portrait-halftone.webp"

DISPLAY_W = 224  # README <img> width; 2 px per cell at 1x
GRID = 112
CELL = 4.0
REVEAL = 1.82  # seconds
FADE = 0.18
MIN_LUM = 0.03  # darker cells are background
LIFT = 0.68  # gamma that lifts shadows so dark hair still reads
DOT_MAX = 0.56  # largest radius, as a share of the cell
SPECK = 0.14  # brighter than every neighbour by this much = a speck
SOFT_EDGE = 24
CARD_BG = "#0d1117"  # light theme: the portrait sits on a dark card

# Dark to light, interpolated into STEPS shades.
STOPS = ("#2e0f07", "#5c1e0e", "#8f3418", "#c05226", "#dc7438", "#e8925a", "#efab7c")
STEPS = 24

Grid = list[list[float]]


def mix(a: str, b: str, f: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(ca, cb))


RAMP = [mix(STOPS[int(t)], STOPS[min(int(t) + 1, len(STOPS) - 1)], t - int(t))
        for t in (i * (len(STOPS) - 1) / (STEPS - 1) for i in range(STEPS))]


def load_pgm(data: bytes) -> Grid:
    """A binary 8-bit PGM as rows of 0..1."""
    fields: list[bytes] = []
    pos = 0
    while len(fields) < 4:  # magic, width, height, maxval
        while data[pos:pos + 1].isspace():
            pos += 1
        start = pos
        while not data[pos:pos + 1].isspace():
            pos += 1
        fields.append(data[start:pos])
    pos += 1
    if fields[0] != b"P5":
        raise ValueError("expected a binary PGM (P5)")
    w, h, top = int(fields[1]), int(fields[2]), int(fields[3])
    pixels = data[pos:pos + w * h]
    return [[pixels[r * w + c] / top for c in range(w)] for r in range(h)]


def resample(src: Grid, n: int) -> Grid:
    """Area-average the square map to n x n."""
    size = len(src)
    scale = size / n

    def spans(i: int) -> list[tuple[int, float]]:
        a, b = i * scale, (i + 1) * scale
        out, k = [], int(a)
        while k < b and k < size:
            out.append((k, min(b, k + 1) - max(a, k)))
            k += 1
        return out

    weights = [spans(i) for i in range(n)]
    return [
        [sum(src[r][k] * wr * wc for r, wr in rows for k, wc in cols) / (scale * scale) for cols in weights]
        for rows in weights
    ]


def despeckle(lum: Grid) -> Grid:
    """Clamp isolated bright cells to their brightest neighbour; drop dots with no lit neighbour."""
    n = len(lum)
    out = [row[:] for row in lum]
    for r in range(n):
        for c in range(n):
            top = max(lum[y][x] for y in range(max(0, r - 1), min(n, r + 2))
                      for x in range(max(0, c - 1), min(n, c + 2)) if (y, x) != (r, c))
            if lum[r][c] > top + SPECK:
                out[r][c] = top
            if top < MIN_LUM:
                out[r][c] = 0.0
    return out


def dots_svg(lum: Grid) -> str:
    """One dot per cell, cropped to the rows with dots."""
    n = len(lum)
    size = n * CELL
    first = next(r for r in range(n) if any(v >= MIN_LUM for v in lum[r]))
    top = max(0, first - 1) * CELL
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {top:g} {size:g} {size - top:g}" '
        f'width="{size:g}" height="{size - top:g}">',
        "<style>" + "".join(f".c{i}{{fill:{c}}}" for i, c in enumerate(RAMP)) + "</style>",
    ]
    for row in range(n):
        for col in range(n):
            if lum[row][col] < MIN_LUM:
                continue
            v = lum[row][col] ** LIFT
            r = CELL * DOT_MAX * v
            if r < CELL * 0.08:
                continue
            shade = min(len(RAMP) - 1, int(v * len(RAMP)))
            out.append(f'<circle class="c{shade}" cx="{(col + .5) * CELL:g}" cy="{(row + .5) * CELL:g}" r="{r:.2f}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def build_dots() -> str:
    return dots_svg(despeckle(resample(load_pgm(SOURCE.read_bytes()), GRID)))


def webp_size(raw: bytes) -> tuple[int, int]:
    """A WebP's canvas size (VP8X, VP8L or VP8 chunk)."""
    kind = raw[12:16]
    if kind == b"VP8X":
        return int.from_bytes(raw[24:27], "little") + 1, int.from_bytes(raw[27:30], "little") + 1
    if kind == b"VP8L":
        bits = int.from_bytes(raw[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return int.from_bytes(raw[26:28], "little") & 0x3FFF, int.from_bytes(raw[28:30], "little") & 0x3FFF


def render(card: bool) -> str:
    w, h = webp_size(RASTER.read_bytes())
    vw, vh = DISPLAY_W, round(DISPLAY_W * h / w)
    total = REVEAL + FADE
    backdrop = f'<rect width="{vw}" height="{vh}" rx="8" fill="{CARD_BG}"/>' if card else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" role="img" aria-label="Halftone portrait of {NAME}">
<defs>
<linearGradient id="edge" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="{vh / (vh + SOFT_EDGE):.4f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<linearGradient id="scan" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#dc7438" stop-opacity="0"/><stop offset="1" stop-color="#efab7c" stop-opacity=".9"/></linearGradient>
<mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="{vw}" height="{vh}"><rect y="0" width="{vw}" height="{vh + SOFT_EDGE}" fill="url(#edge)"><animate attributeName="y" values="{-(vh + SOFT_EDGE)};{-(vh + SOFT_EDGE)};0" keyTimes="0;.02;1" dur="{total:.2f}s" fill="freeze"/></rect></mask>
</defs>
{backdrop}
<image href="{data_uri(RASTER, "image/webp")}" width="{vw}" height="{vh}" mask="url(#reveal)"/>
<rect x="0" y="-7" width="{vw}" height="7" fill="url(#scan)" opacity="0"><animate attributeName="y" values="-7;{vh}" dur="{REVEAL:.2f}s" fill="freeze"/><animate attributeName="opacity" values="0;.8;.8;0" keyTimes="0;.03;.9;1" dur="{total:.2f}s" fill="freeze"/></rect>
</svg>
"""
