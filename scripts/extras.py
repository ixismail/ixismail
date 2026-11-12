"""Generate the README's static extras, light and dark: the typed section headers, the
achievements shelf, the "Ask me about" sticky notes and the hero computer.

Every animation uses the "values" trick (the attributes hold the finished frame; SMIL only rewinds
it at load), so a renderer without SMIL shows the finished drawing.

Usage:  python scripts/extras.py        (stdlib only, writes into assets/)
"""
from __future__ import annotations

import base64
from pathlib import Path

import notes_lettering

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ART = Path(__file__).resolve().parent / "art"

MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "dark": {"card": "#0d1117", "line": "#30363d", "text": "#e6edf3", "muted": "#9198a1",
             "accent": "#f59f1a", "ember": "#f0703c", "link": "#58a6ff"},
    "light": {"card": "#ffffff", "line": "#d0d7de", "text": "#1f2328", "muted": "#59636e",
              "accent": "#b4400c", "ember": "#c43d0e", "link": "#0969da"},
}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def typed(attr: str, steps: list, start: float, step: float, final) -> str:
    """Hold `steps[0]` until `start`, then advance one step every `step` seconds."""
    dur = start + step * len(steps)
    values = [steps[0], *steps, final]
    times = [0.0] + [(start + i * step) / dur for i in range(len(steps))] + [1.0]
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{dur:.2f}s" fill="freeze" '
            f'values="{";".join(str(v) for v in values)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}"/>')


# ---- Section headers: `cd ~/projects` typed out ------------------------------------------------


def header_svg(folder: str, t: dict) -> str:
    """A shell prompt typing `cd ~/<folder>`, then the cursor blinks. The section's real heading
    is the <h2> around the image; this is its look."""
    command = f"cd ~/{folder}"
    char_w, size = 13.2, 22
    w = 40 + (2 + len(command)) * char_w + 30
    x_cmd = 20 + 2 * char_w
    text_w = len(command) * char_w
    widths = [char_w * i for i in range(len(command))]
    cursor = [x_cmd + char_w * i for i in range(len(command))]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} 44" width="{w:.0f}" height="44" role="img" aria-label="~/{folder}">
<defs><clipPath id="type"><rect x="{x_cmd - 2}" y="0" height="44" width="{text_w + 4}">{typed("width", widths, 0.4, 0.07, text_w + 4)}</rect></clipPath></defs>
<text x="20" y="29" font-family="{MONO}" font-size="{size}" font-weight="700" fill="{t["accent"]}">❯</text>
<text x="{x_cmd}" y="29" clip-path="url(#type)" textLength="{text_w}" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="{size}" font-weight="700" fill="{t["text"]}">{esc(command)}</text>
<rect x="{x_cmd + text_w + 4}" y="12" width="11" height="22" fill="{t["accent"]}">{typed("x", cursor, 0.4, 0.07, x_cmd + text_w + 4)}<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
</svg>
'''


# ---- Achievements: the bucket list's ticked goals, as rubber stamps -----------------------------

# The portfolio's bucket list (content/bucket-list/goals.ts), the goals marked done.
ACHIEVEMENTS = (
    ("PORTFOLIO", "SHIPPED", "MAR 2025"),
    ("INTERNSHIP", "LANDED", "MAY 2024"),
    ("MENTORED A", "JUNIOR DEV", "DONE"),
    ("2 SELF-HELP", "BOOKS READ", "DONE"),
    ("NEVER VAPED", "OR SMOKED", "20 YEARS"),
)
TILTS = (-6, 4, -3, 5, -4)


def achievements_svg(t: dict) -> str:
    w, h = 840, 196
    stamps = []
    gap = (w - 48) / len(ACHIEVEMENTS)
    for i, (line1, line2, foot) in enumerate(ACHIEVEMENTS):
        cx, cy = 24 + gap * (i + 0.5), 112
        color = t["ember"] if i % 2 else t["accent"]
        # A double ring (rough: one ring dashed), two words, a footer; pressed in one after another.
        delay = 0.25 + i * 0.22
        press = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{delay / (delay + 0.25):.3f};1" dur="{delay + 0.25:.2f}s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="scale" additive="sum" values="1.25;1.25;1" keyTimes="0;{delay / (delay + 0.25):.3f};1" dur="{delay + 0.25:.2f}s" fill="freeze"/>')
        stamps.append(
            f'<g transform="translate({cx:.1f} {cy}) rotate({TILTS[i]})"><g opacity=".9">{press}'
            f'<circle r="62" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<circle r="55" fill="none" stroke="{color}" stroke-width="1.2" stroke-dasharray="3 3"/>'
            f'<text y="-6" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" letter-spacing="1" fill="{color}">{esc(line1)}</text>'
            f'<text y="12" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" letter-spacing="1" fill="{color}">{esc(line2)}</text>'
            f'<path d="M-30 22H30" stroke="{color}" stroke-width="1"/>'
            f'<text y="38" text-anchor="middle" font-family="{MONO}" font-size="9.5" letter-spacing="2" fill="{color}">{esc(foot)}</text>'
            "</g></g>"
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Achievements unlocked: {esc("; ".join(f"{a} {b} ({c.lower()})" for a, b, c in ACHIEVEMENTS))}.">
<text x="{w / 2}" y="22" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{t["muted"]}">ACHIEVEMENTS UNLOCKED · FROM MY BUCKET LIST</text>
{"".join(stamps)}
</svg>
'''


# ---- "Ask me about": sticky notes, as on the guestbook ----------------------------------------

# The guestbook's papers and inks (components/guestbook/sticky-note.ts).
PAPERS = (("#fff4a3", "#3b3415"), ("#c9f1ff", "#16323d"), ("#ffd6e0", "#43202b"), ("#d9f99d", "#26330f"))
NOTE_TILTS = (-3, 2, -1.5, 3)


def notes_svg(t: dict) -> str:
    w, h, note = 840, 250, 168
    k = 30 / notes_lettering.UNITS_PER_EM  # 30 px handwriting
    gap = (w - 4 * note) / 5
    notes = []
    for i, lines in enumerate(notes_lettering.NOTES):
        paper, ink = PAPERS[i]
        x, y = gap + i * (note + gap), 58
        words = []
        for j, line in enumerate(lines):
            lx = (note - line["advance"] * k) / 2
            words.append(f'<path transform="translate({lx:.1f} {78 + j * 34}) scale({k:.5f} {-k:.5f})" fill="{ink}" d="{line["path"]}"/>')
        notes.append(
            f'<g transform="translate({x + note / 2:.1f} {y + note / 2}) rotate({NOTE_TILTS[i]}) translate({-note / 2} {-note / 2})">'
            f'<rect x="3" y="7" width="{note}" height="{note}" fill="#000" opacity=".22" filter="url(#soft)"/>'
            f'<rect width="{note}" height="{note}" fill="{paper}"/>'
            f'<rect x="{note / 2 - 30}" y="-9" width="60" height="18" fill="#fff" opacity=".55" transform="rotate({-NOTE_TILTS[i] * 1.5} {note / 2} 0)"/>'
            f'{"".join(words)}</g>'
        )
    topics = "; ".join(" ".join(line["text"] for line in lines) for lines in notes_lettering.NOTES)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Ask me about: {esc(topics)}.">
<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter></defs>
<text x="{w / 2}" y="22" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{t["muted"]}">ASK ME ABOUT</text>
{"".join(notes)}
</svg>
'''


# ---- The hero computer --------------------------------------------------------------------------


def hero_svg(t: dict) -> str:
    """A still of the homepage's 3D desk (the site renders it live in three.js), framed."""
    w, h = 410, 260
    image = base64.b64encode((ART / "hero-computer.webp").read_bytes()).decode()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="The 3D desk from my homepage, rendered live in three.js on themuhammadismail.com">
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["card"]}" stroke="{t["line"]}"/>
<text x="20" y="30" font-family="{MONO}" font-size="11" letter-spacing="2.5" fill="{t["muted"]}">ON MY HOMEPAGE</text>
<image href="data:image/webp;base64,{image}" x="25" y="52" width="360" height="135"/>
<text x="20" y="222" font-family="{SANS}" font-size="15" font-weight="600" fill="{t["text"]}">A desk you can turn around</text>
<text x="20" y="242" font-family="{SANS}" font-size="12.5" fill="{t["muted"]}">Rendered live with three.js · <tspan fill="{t["link"]}">themuhammadismail.com ↗</tspan></text>
</svg>
'''


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        files = {
            f"header-projects-{name}.svg": header_svg("projects", theme),
            f"header-toolbox-{name}.svg": header_svg("toolbox", theme),
            f"achievements-{name}.svg": achievements_svg(theme),
            f"notes-{name}.svg": notes_svg(theme),
            f"hero-{name}.svg": hero_svg(theme),
        }
        for fname, svg in files.items():
            (ASSETS / fname).write_text(svg, encoding="utf-8", newline="\n")
            print("wrote", fname)
