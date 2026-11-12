"""Generate the README's typed name, tagline and site link (light and dark).

Every animation uses the "values" trick: the element's own attributes hold the
finished state, and SMIL only rewinds it at load. A renderer without SMIL shows
the final frame instead of an empty box.

Usage:  python scripts/readme_assets.py        (stdlib only, writes into assets/)
"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

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


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    files = {
        "name-dark.svg": name_svg(AMBER, "#ffffff", "#1f6feb"),
        "name-light.svg": name_svg("#b4400c", "#1f2328", "#0550ae"),
    }
    for fname, svg in files.items():
        (ASSETS / fname).write_text(svg, encoding="utf-8")
        print("wrote", ASSETS / fname)
