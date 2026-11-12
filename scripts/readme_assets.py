"""Generate the README's text images, light and dark: the typed name with its tagline and site
link, the "Thanks For Visiting!" sign-off and the "Back to top" button.

Every animation uses the "values" trick: the element's own attributes hold the
finished state, and SMIL only rewinds it at load. A renderer without SMIL shows
the final frame instead of an empty box.

Usage:  python scripts/readme_assets.py        (stdlib only, writes into assets/)
"""
import base64
from pathlib import Path

import cta_lettering
import lettering

ASSETS = Path(__file__).resolve().parent.parent / "assets"
CTA_ART = Path(__file__).resolve().parent / "cta-art"

NAME = "Muhammad Ismail"
TAGLINE = "Full Stack Software Engineer"
SITE = "themuhammadismail.com"

MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
AMBER = "#f59f1a"
TYPE_START = 1.82    # name starts typing once the portrait reveal is done
TYPE_STEP = 0.1      # seconds per character


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def discrete(attr: str, steps: list, start: float, step: float, final) -> str:
    """Hold `steps[0]` until `start`, then advance one step every `step` seconds."""
    dur = start + step * len(steps)
    values = [steps[0]] + steps + [final]
    times = [0.0] + [(start + i * step) / dur for i in range(len(steps))] + [1.0]
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{dur:.2f}s" fill="freeze" '
            f'values="{";".join(str(v) for v in values)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}"/>')


def fade_in(at: float, length: float = 0.6) -> str:
    dur = at + length
    return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{at / dur:.4f};1" '
            f'dur="{dur:.2f}s" fill="freeze"/>')


def name_svg(name_color: str, sub_color: str, link_color: str) -> str:
    """The name types itself out; the tagline, then the site link (the whole image links to
    the site, so the link line is drawn here, in our own blue, tight under the tagline)."""
    w, char_w = 560, 22
    text_w = char_w * len(NAME)
    x0 = (w - text_w) // 2
    widths = [char_w * i for i in range(len(NAME))]
    cursor_x = [x0 + char_w * i for i in range(len(NAME))]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 120" width="{w}" height="120" role="img" aria-label="{esc(NAME)}, {esc(TAGLINE)}. {SITE}">
<defs><clipPath id="typed"><rect x="{x0 - 5}" y="0" height="70" width="{text_w + 10}">{discrete("width", widths, TYPE_START, TYPE_STEP, text_w + 10)}</rect></clipPath></defs>
<text x="{x0}" y="52" clip-path="url(#typed)" textLength="{text_w}" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="34" font-weight="700" fill="{name_color}">{esc(NAME)}</text>
<rect x="{x0 + text_w + 6}" y="24" width="13" height="34" fill="{name_color}">{discrete("x", cursor_x, TYPE_START, TYPE_STEP, x0 + text_w + 6)}<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
<text x="{w // 2}" y="86" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="1" fill="{sub_color}">{esc(TAGLINE)}{fade_in(TYPE_START + TYPE_STEP * len(NAME) + 0.1)}</text>
<text x="{w // 2}" y="112" text-anchor="middle" font-family="{SANS}" font-size="16" font-weight="500" fill="{link_color}">{SITE} ↗{fade_in(TYPE_START + TYPE_STEP * len(NAME) + 0.4)}</text>
</svg>
'''


def thanks_svg(color: str) -> str:
    """The sign-off in Pacifico outlines (scripts/lettering.py), written in left to right: a mask
    with a soft leading edge slides across, as if the ink were going down."""
    w, h, width = 420, 90, 340  # the lettering spans `width` px, centred
    k = width / (lettering.MAX_X - lettering.MIN_X)
    tx = (w - width) / 2 - lettering.MIN_X * k
    ty = (h - (lettering.MAX_Y - lettering.MIN_Y) * k) / 2 + lettering.MAX_Y * k
    edge = 40  # the soft edge's width, px
    span = w + edge
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{lettering.TEXT}">
<defs>
<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset="{w / span:.4f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="ink" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}"><rect x="0" y="0" width="{span}" height="{h}" fill="url(#edge)"><animate attributeName="x" values="{-span};{-span};0" keyTimes="0;.12;1" calcMode="spline" keySplines="0 0 1 1;.45 0 .25 1" dur="2s" fill="freeze"/></rect></mask>
</defs>
<g mask="url(#ink)"><path transform="translate({tx:.2f} {ty:.2f}) scale({k:.6f} {-k:.6f})" fill="{color}" d="{lettering.PATH}"/></g>
</svg>
'''


def top_svg(color: str) -> str:
    """"Back to top": an outlined pill, its arrow bobbing up now and then."""
    w, h = 134, 36
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Back to top">
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{(h - 1) / 2}" fill="{color}" fill-opacity=".06" stroke="{color}" stroke-opacity=".5"/>
<g transform="translate(24 18)"><path d="M0 6V-6M-4.5-1.5L0-6L4.5-1.5" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0;0 0" keyTimes="0;.2;.4;1" dur="2.4s" repeatCount="indefinite"/></path></g>
<text x="40" y="22.5" textLength="76" lengthAdjust="spacingAndGlyphs" font-family="{SANS}" font-size="13" font-weight="600" fill="{color}">Back to top</text>
</svg>
'''


# ---- The closing call to action ----------------------------------------------------------------
#
# The portfolio's closing CTA, drawn as one image: everything sits where the site puts it, in the
# site's own panel units (1215 × 674 CSS px, measured on a 1280 px wide page), and the image scales
# it down. The ocean is a real frame of the site's ASCII ocean (scripts/cta-art/ocean-*.webp); the
# wings, seal and logo are the site's own artwork; the words are outlines (scripts/cta_lettering.py).

CTA_W, CTA_H, CTA_CX = 1215, 674, 607.5

CTA_THEMES = {
    "dark": {
        "panel": "#171717", "hatch": "#ffffff", "hatch_opacity": 0.025, "pool": "23,23,23",
        "ink": "#ffffff", "accent": "#f87171", "muted": "rgba(255,255,255,0.6)",
        "line": "rgba(255,255,255,0.1)", "corner": "rgba(255,255,255,0.35)",
        "button": "#232326", "button_line": "rgba(255,255,255,0.1)", "chip": "#fafafa", "arrow": "#000000",
        "invert_wings": False,
    },
    "light": {
        "panel": "#fafafa", "hatch": "#000000", "hatch_opacity": 0.035, "pool": "250,250,250",
        "ink": "#000000", "accent": "#b91c1c", "muted": "rgba(0,0,0,0.6)",
        "line": "rgba(0,0,0,0.1)", "corner": "rgba(0,0,0,0.35)",
        "button": "#ffffff", "button_line": "rgba(0,0,0,0.1)", "chip": "#000000", "arrow": "#ffffff",
        "invert_wings": True,
    },
}

# Octicons "arrow-right" (MIT), the site's GoArrowRight, 16 × 16.
ARROW_RIGHT = (
    "M8.22 2.97a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.751.751 0 0 1-1.042-.018"
    ".751.751 0 0 1-.018-1.042l2.97-2.97H3.75a.75.75 0 0 1 0-1.5h7.44L8.22 4.03a.75.75 0 0 1 0-1.06Z"
)


def art(name: str, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode((CTA_ART / name).read_bytes()).decode()}"


def run_width(name: str, size: float) -> float:
    run = cta_lettering.RUNS[name]
    return run["advance"] * size / cta_lettering.FONTS[run["font"]]["upem"]


def run_baseline(name: str, top: float, line_height: float, size: float) -> float:
    """Where a browser puts the baseline in a line box: the font's ascent + descent centred."""
    font = cta_lettering.FONTS[cta_lettering.RUNS[name]["font"]]
    k = size / font["upem"]
    ascent, descent = font["ascender"] * k, -font["descender"] * k
    return top + (line_height - (ascent + descent)) / 2 + ascent


def run_path(name: str, x: float, baseline: float, size: float, fill: str) -> str:
    run = cta_lettering.RUNS[name]
    k = size / cta_lettering.FONTS[run["font"]]["upem"]
    return (f'<path transform="translate({x:.2f} {baseline:.2f}) scale({k:.5f} {-k:.5f})" '
            f'fill="{fill}" d="{run["path"]}"/>')


def swash(x: float, width: float, line_top: float, color: str, delay: float) -> str:
    """The SwashAccent stroke (viewBox 120 × 16, stretched): 112 % of the word, its bottom 0.18 em
    below the line box, 0.22 em tall; it draws itself in, left to right."""
    box_x, box_w, box_h = x - 0.06 * width, 1.12 * width, 13.2
    box_y = line_top + 67.2 + 10.8 - box_h

    def at(px: float, py: float) -> str:
        return f"{box_x + px * box_w / 120:.2f} {box_y + py * box_h / 16:.2f}"

    dur = delay + 0.9
    return (f'<path d="M{at(2, 11)}C{at(30, 3)} {at(70, 3)} {at(118, 9)}" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;{delay / dur:.3f};1" '
            f'calcMode="spline" keySplines="0 0 1 1;.4 0 .2 1" dur="{dur:.2f}s" fill="freeze"/></path>')


def cta_svg(theme: str) -> str:
    t = CTA_THEMES[theme]
    parts = []

    # The headline: two lines of 60 px on 67.2 px, each an italic lead and an upright red accent.
    for i, (lead, accent) in enumerate((("lead1", "accent1"), ("lead2", "accent2"))):
        top = 254 + i * 67.2
        lead_w, accent_w = run_width(lead, 60), run_width(accent, 60)
        x0 = CTA_CX - (lead_w + accent_w) / 2
        parts.append(run_path(lead, x0, run_baseline(lead, top, 67.2, 60), 60, t["ink"]))
        parts.append(run_path(accent, x0 + lead_w, run_baseline(accent, top, 67.2, 60), 60, t["accent"]))
        parts.append(swash(x0 + lead_w, accent_w, top, t["accent"], 0.5 + i * 0.35))

    # "Start a conversation": a pill (24 px before the words, 14 px gap, a 40 px chip, 6 px after).
    bw = 1 + 24 + run_width("action", 16) + 14 + 40 + 6 + 1
    bx, by, bh = CTA_CX - bw / 2, 424.4, 54
    chip_x, chip_y = bx + bw - 1 - 6 - 20, by + bh / 2
    parts.append(f'<rect x="{bx + 0.5:.2f}" y="{by + 0.5}" width="{bw - 1:.2f}" height="{bh - 1}" '
                 f'rx="{(bh - 1) / 2}" fill="{t["button"]}" stroke="{t["button_line"]}"/>')
    parts.append(run_path("action", bx + 25, run_baseline("action", by + (bh - 24) / 2, 24, 16), 16, t["ink"]))
    parts.append(f'<circle cx="{chip_x:.2f}" cy="{chip_y:.2f}" r="20" fill="{t["chip"]}"/>')
    parts.append(f'<path transform="translate({chip_x - 8:.2f} {chip_y - 8:.2f})" fill="{t["arrow"]}" d="{ARROW_RIGHT}"/>')

    # The availability line (upright serif, 24 / 36) and the ask (Outfit, 16 / 24, 60 %).
    for name, top, lh, size, fill in (("availability", 522.4, 36, 24, t["ink"]), ("ask", 570.4, 24, 16, t["muted"])):
        parts.append(run_path(name, CTA_CX - run_width(name, size) / 2, run_baseline(name, top, lh, size), size, fill))

    wings = ' filter="url(#invert)"' if t["invert_wings"] else ""
    disc = '<circle cx="607.5" cy="158.2" r="35" fill="#0b1433"/>' if t["invert_wings"] else ""
    corners = "".join(f'<rect x="{x}" y="{y}" width="6" height="6" fill="{t["corner"]}"/>'
                      for x in (1, CTA_W - 7) for y in (1, CTA_H - 7))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CTA_W} {CTA_H}" width="840" height="{CTA_H * 840 / CTA_W:.0f}" role="img" aria-label="Got an idea worth building? Let's talk it through. Start a conversation. I'm taking on freelance projects and open to full-time roles. Tell me what you're working on.">
<defs>
<clipPath id="panel"><rect x="1" y="1" width="{CTA_W - 2}" height="{CTA_H - 2}"/></clipPath>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1" height="7" fill="{t["hatch"]}" fill-opacity="{t["hatch_opacity"]}"/></pattern>
<radialGradient id="pool" cx=".5" cy=".52" r=".5" gradientTransform="translate(.5 .52) scale(.72 .88) translate(-.5 -.52)"><stop offset="0" stop-color="rgb({t["pool"]})" stop-opacity=".88"/><stop offset=".55" stop-color="rgb({t["pool"]})" stop-opacity=".55"/><stop offset="1" stop-color="rgb({t["pool"]})" stop-opacity="0"/></radialGradient>
<filter id="invert" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="-1 0 0 0 1 0 -1 0 0 1 0 0 -1 0 1 0 0 0 1 0"/></filter>
</defs>
<rect width="{CTA_W}" height="{CTA_H}" fill="{t["panel"]}"/>
<g clip-path="url(#panel)">
<rect width="{CTA_W}" height="{CTA_H}" fill="url(#hatch)"/>
<image href="{art(f"ocean-{theme}.webp", "image/webp")}" x="1" y="1" width="1213" height="673" preserveAspectRatio="none"><animateTransform attributeName="transform" type="translate" values="0 0;-10 4;0 0" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="16s" repeatCount="indefinite"/></image>
<rect width="{CTA_W}" height="{CTA_H}" fill="url(#pool)"/>
</g>
<rect x=".5" y=".5" width="{CTA_W - 1}" height="{CTA_H - 1}" fill="none" stroke="{t["line"]}"/>
{corners}
<image href="{art("wing-left.svg", "image/svg+xml")}" x="394.5" y="81" width="168" height="149"{wings}/>
<image href="{art("wing-right.svg", "image/svg+xml")}" x="652.5" y="81" width="168" height="149"{wings}/>
{disc}<image href="{art("seal.svg", "image/svg+xml")}" x="554.5" y="105.2" width="106" height="106"/>
<image href="{art("logo.webp", "image/webp")}" x="583.5" y="143.2" width="48" height="30"/>
{"".join(parts)}
</svg>
'''


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    files = {
        "name-dark.svg": name_svg(AMBER, "#ffffff", "#1f6feb"),
        "name-light.svg": name_svg("#b4400c", "#1f2328", "#0550ae"),
        # The sign-off and its button: GitHub's link blue, light on dark and deep on light.
        "thanks-dark.svg": thanks_svg("#58a6ff"),
        "thanks-light.svg": thanks_svg("#0969da"),
        "top-dark.svg": top_svg("#58a6ff"),
        "top-light.svg": top_svg("#0969da"),
        # The closing call to action, as on the portfolio.
        "cta-dark.svg": cta_svg("dark"),
        "cta-light.svg": cta_svg("light"),
    }
    for fname, svg in files.items():
        (ASSETS / fname).write_text(svg, encoding="utf-8")
        print("wrote", ASSETS / fname)
