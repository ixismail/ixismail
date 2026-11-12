"""The portfolio's closing CTA as one image, laid out in the site's own CSS px (1215 x 674)."""
from __future__ import annotations

from dataclasses import dataclass

from profilegen import icons
from profilegen.config import ART
from profilegen.lettering import cta as lettering
from profilegen.svg import data_uri

W, H, CX = 1215, 674, 607.5
DISPLAY_W = 840
CTA_ART = ART / "cta"
LABEL = ("Got an idea worth building? Let's talk it through. Start a conversation. I'm taking on "
         "freelance projects and open to full-time roles. Tell me what you're working on.")


@dataclass(frozen=True)
class CtaPalette:
    panel: str
    hatch: str
    hatch_opacity: float
    pool: str  # "r,g,b"
    ink: str
    accent: str
    muted: str
    line: str
    corner: str
    button: str
    button_line: str
    chip: str
    arrow: str
    invert_wings: bool  # the wing artwork is white


PALETTES = {
    "dark": CtaPalette(
        panel="#171717", hatch="#ffffff", hatch_opacity=0.025, pool="23,23,23",
        ink="#ffffff", accent="#f87171", muted="rgba(255,255,255,0.6)",
        line="rgba(255,255,255,0.1)", corner="rgba(255,255,255,0.35)",
        button="#232326", button_line="rgba(255,255,255,0.1)", chip="#fafafa", arrow="#000000",
        invert_wings=False,
    ),
    "light": CtaPalette(
        panel="#fafafa", hatch="#000000", hatch_opacity=0.035, pool="250,250,250",
        ink="#000000", accent="#b91c1c", muted="rgba(0,0,0,0.6)",
        line="rgba(0,0,0,0.1)", corner="rgba(0,0,0,0.35)",
        button="#ffffff", button_line="rgba(0,0,0,0.1)", chip="#000000", arrow="#ffffff",
        invert_wings=True,
    ),
}


def run_width(name: str, size: float) -> float:
    run = lettering.RUNS[name]
    return float(run["advance"]) * size / lettering.FONTS[run["font"]]["upem"]


def run_baseline(name: str, top: float, line_height: float, size: float) -> float:
    """The baseline a browser uses: ascent + descent centred in the line box."""
    font = lettering.FONTS[lettering.RUNS[name]["font"]]
    k = size / font["upem"]
    ascent, descent = font["ascender"] * k, -font["descender"] * k
    return top + (line_height - (ascent + descent)) / 2 + ascent


def run_path(name: str, x: float, baseline: float, size: float, fill: str) -> str:
    run = lettering.RUNS[name]
    k = size / lettering.FONTS[run["font"]]["upem"]
    return (f'<path transform="translate({x:.2f} {baseline:.2f}) scale({k:.5f} {-k:.5f})" '
            f'fill="{fill}" d="{run["path"]}"/>')


def swash(x: float, width: float, line_top: float, color: str, delay: float) -> str:
    """The site's SwashAccent underline (120 x 16 viewBox), drawing itself in."""
    box_x, box_w, box_h = x - 0.06 * width, 1.12 * width, 13.2
    box_y = line_top + 67.2 + 10.8 - box_h

    def at(px: float, py: float) -> str:
        return f"{box_x + px * box_w / 120:.2f} {box_y + py * box_h / 16:.2f}"

    dur = delay + 0.9
    return (f'<path d="M{at(2, 11)}C{at(30, 3)} {at(70, 3)} {at(118, 9)}" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{delay / dur:.3f};1" '
            f'calcMode="spline" keySplines="0 0 1 1;.4 0 .2 1" dur="{dur:.2f}s" fill="freeze"/></path>')


def _words(p: CtaPalette) -> str:
    parts = []
    # Headline: two 60/67.2 px lines, an italic lead then an upright accent.
    for i, (lead, accent) in enumerate((("lead1", "accent1"), ("lead2", "accent2"))):
        top = 254 + i * 67.2
        lead_w, accent_w = run_width(lead, 60), run_width(accent, 60)
        x0 = CX - (lead_w + accent_w) / 2
        parts.append(run_path(lead, x0, run_baseline(lead, top, 67.2, 60), 60, p.ink))
        parts.append(run_path(accent, x0 + lead_w, run_baseline(accent, top, 67.2, 60), 60, p.accent))
        parts.append(swash(x0 + lead_w, accent_w, top, p.accent, 0.5 + i * 0.35))

    # Button: 24 px padding, label, 14 px gap, 40 px chip, 6 px padding.
    bw = 1 + 24 + run_width("action", 16) + 14 + 40 + 6 + 1
    bx, by, bh = CX - bw / 2, 424.4, 54
    chip_x, chip_y = bx + bw - 1 - 6 - 20, by + bh / 2
    parts.append(f'<rect x="{bx + 0.5:.2f}" y="{by + 0.5}" width="{bw - 1:.2f}" height="{bh - 1}" '
                 f'rx="{(bh - 1) / 2}" fill="{p.button}" stroke="{p.button_line}"/>')
    parts.append(run_path("action", bx + 25, run_baseline("action", by + (bh - 24) / 2, 24, 16), 16, p.ink))
    parts.append(f'<circle cx="{chip_x:.2f}" cy="{chip_y:.2f}" r="20" fill="{p.chip}"/>')
    parts.append(f'<path transform="translate({chip_x - 8:.2f} {chip_y - 8:.2f})" fill="{p.arrow}" d="{icons.ARROW_RIGHT}"/>')

    for name, top, lh, size, fill in (("availability", 522.4, 36, 24, p.ink), ("ask", 570.4, 24, 16, p.muted)):
        parts.append(run_path(name, CX - run_width(name, size) / 2, run_baseline(name, top, lh, size), size, fill))
    return "".join(parts)


def render(theme: str) -> str:
    p = PALETTES[theme]
    wings = ' filter="url(#invert)"' if p.invert_wings else ""
    disc = '<circle cx="607.5" cy="158.2" r="35" fill="#0b1433"/>' if p.invert_wings else ""
    corners = "".join(f'<rect x="{x}" y="{y}" width="6" height="6" fill="{p.corner}"/>'
                      for x in (1, W - 7) for y in (1, H - 7))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{DISPLAY_W}" height="{H * DISPLAY_W / W:.0f}" role="img" aria-label="{LABEL}">
<defs>
<clipPath id="panel"><rect x="1" y="1" width="{W - 2}" height="{H - 2}"/></clipPath>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1" height="7" fill="{p.hatch}" fill-opacity="{p.hatch_opacity}"/></pattern>
<radialGradient id="pool" cx=".5" cy=".52" r=".5" gradientTransform="translate(.5 .52) scale(.72 .88) translate(-.5 -.52)"><stop offset="0" stop-color="rgb({p.pool})" stop-opacity=".88"/><stop offset=".55" stop-color="rgb({p.pool})" stop-opacity=".55"/><stop offset="1" stop-color="rgb({p.pool})" stop-opacity="0"/></radialGradient>
<filter id="invert" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="-1 0 0 0 1 0 -1 0 0 1 0 0 -1 0 1 0 0 0 1 0"/></filter>
</defs>
<rect width="{W}" height="{H}" fill="{p.panel}"/>
<g clip-path="url(#panel)">
<rect width="{W}" height="{H}" fill="url(#hatch)"/>
<image href="{data_uri(CTA_ART / f"ocean-{theme}.webp", "image/webp")}" x="1" y="1" width="1213" height="673" preserveAspectRatio="none"><animateTransform attributeName="transform" type="translate" values="0 0;-10 4;0 0" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="16s" repeatCount="indefinite"/></image>
<rect width="{W}" height="{H}" fill="url(#pool)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{p.line}"/>
{corners}
<image href="{data_uri(CTA_ART / "wing-left.svg", "image/svg+xml")}" x="394.5" y="81" width="168" height="149"{wings}/>
<image href="{data_uri(CTA_ART / "wing-right.svg", "image/svg+xml")}" x="652.5" y="81" width="168" height="149"{wings}/>
{disc}<image href="{data_uri(CTA_ART / "seal.svg", "image/svg+xml")}" x="554.5" y="105.2" width="106" height="106"/>
<image href="{data_uri(CTA_ART / "logo.webp", "image/webp")}" x="583.5" y="143.2" width="48" height="30"/>
{_words(p)}
</svg>
'''
