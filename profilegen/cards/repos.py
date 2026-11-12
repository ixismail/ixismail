"""Pinned repo cards, and the README block that lays them out two a row."""
from __future__ import annotations

from collections.abc import Sequence

from profilegen import icons
from profilegen.github.model import Repo
from profilegen.svg import MONO, SANS, esc
from profilegen.theme import Palette

W, H = 410, 150
DESCRIPTION_CHARS, DESCRIPTION_LINES = 56, 2
MONO_CHAR_W = 7  # 11 px monospace


def wrap(text: str, width: int, lines: int) -> list[str]:
    """Wrap to at most `lines` lines of `width` characters, ellipsing the overflow."""
    out: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if len(candidate) <= width:
            line = candidate
            continue
        out.append(line)
        line = word
        if len(out) == lines:
            last = out[-1]
            while len(last) > width - 1 and " " in last:
                last = last.rsplit(" ", 1)[0]
            out[-1] = last.rstrip(",.;:-") + "…"
            return out
    if line:
        out.append(line)
    return out


def alt_text(repo: Repo) -> str:
    return f"{repo.name}: {repo.description}".rstrip(": ")


def render(repo: Repo, t: Palette) -> str:
    lines = wrap(repo.description or "No description yet.", DESCRIPTION_CHARS, DESCRIPTION_LINES)
    description = "".join(
        f'<text x="20" y="{70 + i * 19}" font-family="{SANS}" font-size="12.5" fill="{t.muted}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    meta, x = [], 20
    if repo.language:
        meta.append(f'<circle cx="{x + 5}" cy="124" r="5" fill="{repo.color}"/>'
                    f'<text x="{x + 16}" y="128" font-family="{MONO}" font-size="11" fill="{t.muted}">{esc(repo.language)}</text>')
        x += 16 + MONO_CHAR_W * len(repo.language) + 18
    for icon, value in ((icons.STAR, repo.stars), (icons.FORK, repo.forks)):
        meta.append(f'<path transform="translate({x} 117) scale(.875)" fill="{t.muted}" d="{icon}"/>'
                    f'<text x="{x + 19}" y="128" font-family="{MONO}" font-size="11" fill="{t.muted}">{value:,}</text>')
        x += 19 + MONO_CHAR_W * len(f"{value:,}") + 18
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(alt_text(repo))}">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t.card}" stroke="{t.line}"/>
<path transform="translate(20 22)" fill="{t.muted}" d="{icons.REPO}"/>
<text x="44" y="35" font-family="{SANS}" font-size="15" font-weight="600" fill="{t.link}">{esc(repo.name)}</text>
<path d="M{W - 30} 32L{W - 22} 24M{W - 28} 24H{W - 22}V30" fill="none" stroke="{t.muted}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
{description}
{"".join(meta)}
</svg>
'''


def filename(index: int, theme: str) -> str:
    return f"repo-{index}-{theme}.svg"


def readme_block(pinned: Sequence[Repo]) -> str:
    cells = [
        f'  <a href="{repo.url}">\n'
        f'    <picture>\n'
        f'      <source media="(prefers-color-scheme: dark)" srcset="assets/{filename(i, "dark")}">\n'
        f'      <img src="assets/{filename(i, "light")}" width="{W}" alt="{esc(alt_text(repo))}">\n'
        f'    </picture>\n'
        f'  </a>'
        for i, repo in enumerate(pinned, start=1)
    ]
    rows = ["\n".join(cells[i:i + 2]) for i in range(0, len(cells), 2)]
    return "\n".join(f'<p align="center">\n{row}\n</p>' for row in rows)
