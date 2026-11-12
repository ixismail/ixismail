"""Generate the README's text-based SVGs: typed name, portfolio button, stats card.

Every animation uses the "values" trick: the element's own attributes hold the
finished state, and SMIL only rewinds it at load. A renderer without SMIL shows
the final frame instead of an empty box.

Usage:  python scripts/readme_assets.py        (stdlib only, writes into assets/)
"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

NAME = "Muhammad Ismail"
TAGLINE = "full-stack & backend engineer · go · typescript · postgresql"
SITE = "themuhammadismail.com"
STATS = [  # (big number, label line 1, label line 2)
    ("17,000+", "users across", "production platforms"),
    ("-94%", "shop page query time", "104 ms → 6.3 ms"),
    ("~1,650", "card payments", "processed every month"),
    ("42,000", "product variants in", "one shared catalogue"),
]

MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
AMBER, EMBER, INK = "#f59f1a", "#c43d0e", "#0d1117"
TYPE_START = 3.6     # name starts typing once the portrait reveal is done
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


def name_svg(name_color: str, sub_color: str) -> str:
    w, char_w = 560, 22
    text_w = char_w * len(NAME)
    x0 = (w - text_w) // 2
    widths = [char_w * i for i in range(len(NAME))]
    cursor_x = [x0 + char_w * i for i in range(len(NAME))]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 96" width="{w}" height="96" role="img" aria-label="{esc(NAME)}, {esc(TAGLINE)}">
<defs><clipPath id="typed"><rect x="{x0 - 5}" y="0" height="70" width="{text_w + 10}">{discrete("width", widths, TYPE_START, TYPE_STEP, text_w + 10)}</rect></clipPath></defs>
<text x="{x0}" y="52" clip-path="url(#typed)" textLength="{text_w}" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="34" font-weight="700" fill="{name_color}">{esc(NAME)}</text>
<rect x="{x0 + text_w + 6}" y="24" width="13" height="34" fill="{name_color}">{discrete("x", cursor_x, TYPE_START, TYPE_STEP, x0 + text_w + 6)}<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
<text x="{w // 2}" y="86" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="1" fill="{sub_color}">{esc(TAGLINE)}{fade_in(TYPE_START + TYPE_STEP * len(NAME) + 0.1)}</text>
</svg>
'''


def cta_svg() -> str:
    """Quiet card: thin border, off-white URL, one amber underline that draws in once."""
    url_w = 226
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 80" width="440" height="80" role="img" aria-label="Visit my portfolio at {SITE}">
<rect x=".5" y=".5" width="439" height="79" rx="12" fill="{INK}" stroke="#30363d"/>
<circle cx="29" cy="28" r="3" fill="{AMBER}"/>
<text x="40" y="32" font-family="{MONO}" font-size="10" letter-spacing="2.5" fill="#8b949e">PORTFOLIO</text>
<text x="24" y="56" textLength="{url_w}" lengthAdjust="spacingAndGlyphs" font-family="{SANS}" font-size="20" font-weight="600" fill="#e6edf3">{SITE}</text>
<path d="M24 64H{24 + url_w}" stroke="{AMBER}" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="{url_w}" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" values="{url_w};{url_w};0" keyTimes="0;.35;1" dur="1.3s" fill="freeze"/></path>
<g transform="translate(400 40)">
<circle r="17" fill="{AMBER}" fill-opacity=".08" stroke="{AMBER}" stroke-opacity=".55"/>
<path d="M-6 0H6M1-5L6 0L1 5" fill="none" stroke="{AMBER}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;2.5 0;0 0" dur="2.4s" repeatCount="indefinite"/></path>
</g>
</svg>
'''


def stats_svg() -> str:
    cols = []
    for i, (big, l1, l2) in enumerate(STATS):
        x = 32 + i * 200
        at = 0.3 + i * 0.25
        cols.append(
            f'<g>{fade_in(at, 0.5)}'
            f'<text x="{x}" y="96" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-1" fill="{AMBER}">{esc(big)}</text>'
            f'<text x="{x}" y="122" font-family="{SANS}" font-size="13" fill="#e6edf3">{esc(l1)}</text>'
            f'<text x="{x}" y="140" font-family="{SANS}" font-size="13" fill="#9198a1">{esc(l2)}</text></g>'
        )
        if i:
            cols.append(f'<path d="M{x - 18} 64V144" stroke="#30363d"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 176" width="840" height="176" role="img" aria-label="In production: {"; ".join(f"{b} {a} {c}" for b, a, c in STATS)}. See the work at {SITE}">
<defs><pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{AMBER}" fill-opacity=".07"/></pattern></defs>
<rect x="1" y="1" width="838" height="174" rx="14" fill="{INK}" stroke="#30363d"/>
<rect x="1" y="1" width="838" height="174" rx="14" fill="url(#dots)"/>
<text x="32" y="36" font-family="{MONO}" font-size="11" letter-spacing="3" fill="#9198a1">IN PRODUCTION</text>
<text x="808" y="36" text-anchor="end" font-family="{MONO}" font-size="12" fill="{AMBER}">see the work → {SITE}</text>
{"".join(cols)}
</svg>
'''


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    files = {
        "name-dark.svg": name_svg(AMBER, "#9198a1"),
        "name-light.svg": name_svg("#b4400c", "#59636e"),
        "cta-portfolio.svg": cta_svg(),
        "stats.svg": stats_svg(),
    }
    for fname, svg in files.items():
        (ASSETS / fname).write_text(svg, encoding="utf-8")
        print("wrote", ASSETS / fname)
