"""Blog post cards (cover, title, excerpt, date · category), and the README block that lays them out.

Same frame as the pinned-repo cards, a cover on top. The cover is embedded as a data URI: an SVG
shown as an <img> can't load outside images. Without a usable cover the card draws a quiet band.
"""
from __future__ import annotations

import base64
from collections.abc import Sequence

from profilegen.blog import Post
from profilegen.cards.repos import wrap
from profilegen.config import FEED_URL, SITE
from profilegen.svg import MONO, SANS, esc
from profilegen.theme import Palette

W, H = 410, 326
COVER_H = 200
TITLE_CHARS = 42
EXCERPT_CHARS, EXCERPT_LINES = 56, 2
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
UTM = "utm_source=github&utm_medium=profile"


def date_label(post: Post) -> str:
    """"Nov 12, 2026" (by hand: locale month names differ between machines)."""
    day = post.published
    return f"{MONTHS[day.month - 1]} {day.day}, {day.year}"


def alt_text(post: Post) -> str:
    return f"{post.title}: {post.excerpt}".rstrip(": ") if post.excerpt else post.title


def link(post: Post, index: int) -> str:
    joiner = "&" if "?" in post.url else "?"
    return f"{post.url}{joiner}{UTM}&utm_content=post-{index}"


def _cover(post: Post, t: Palette) -> str:
    if post.cover and post.cover_mime:
        data = base64.b64encode(post.cover).decode()
        return (f'<image href="data:{post.cover_mime};base64,{data}" x="0" y="0" width="{W}" height="{COVER_H}" '
                f'preserveAspectRatio="xMidYMid slice" clip-path="url(#cover)"/>')
    # No usable cover (it couldn't be fetched): a dot grid and the site's name, not an empty box.
    return (f'<pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse">'
            f'<circle cx="7" cy="7" r="1.2" fill="{t.line}"/></pattern>'
            f'<rect x="0" y="0" width="{W}" height="{COVER_H}" fill="url(#dots)" clip-path="url(#cover)"/>'
            f'<text x="{W / 2:.0f}" y="{COVER_H / 2 + 5:.0f}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="13" fill="{t.muted}">{esc(SITE)}</text>')


def render(post: Post, t: Palette) -> str:
    # A long title takes a second line; the excerpt then gives one up, so every card is the same height.
    titles = wrap(post.title, TITLE_CHARS, 2)
    title = "".join(
        f'<text x="20" y="{COVER_H + 32 + i * 20}" font-family="{SANS}" font-size="15" font-weight="600" fill="{t.link}">{esc(line)}</text>'
        for i, line in enumerate(titles)
    )
    excerpt_top = COVER_H + 36 + 20 * len(titles)
    excerpt = "".join(
        f'<text x="20" y="{excerpt_top + i * 19}" font-family="{SANS}" font-size="12.5" fill="{t.muted}">{esc(line)}</text>'
        for i, line in enumerate(wrap(post.excerpt, EXCERPT_CHARS, EXCERPT_LINES - (len(titles) - 1)))
    )
    meta = " · ".join(part for part in (date_label(post), post.category) if part)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(alt_text(post))}">
<defs><clipPath id="cover"><path d="M12.5 .5H{W - 12.5}A12 12 0 0 1 {W - .5} 12.5V{COVER_H}H.5V12.5A12 12 0 0 1 12.5 .5Z"/></clipPath></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t.card}"/>
{_cover(post, t)}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{t.line}"/>
<path d="M.5 {COVER_H}H{W - .5}" stroke="{t.line}"/>
{title}
<path d="M{W - 30} {COVER_H + 30}L{W - 22} {COVER_H + 22}M{W - 28} {COVER_H + 22}H{W - 22}V{COVER_H + 28}" fill="none" stroke="{t.muted}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
{excerpt}
<text x="20" y="{H - 20}" font-family="{MONO}" font-size="11" fill="{t.muted}">{esc(meta)}</text>
</svg>
'''


def filename(index: int, theme: str) -> str:
    return f"post-{index}-{theme}.svg"


def readme_block(posts: Sequence[Post]) -> str:
    """The ~/writing heading, the cards two a row, and a line to every post. Empty without posts."""
    if not posts:
        return ""
    heading = (
        '<h2 align="center">\n'
        '  <picture>\n'
        '    <source media="(prefers-color-scheme: dark)" srcset="assets/header-writing-dark.svg">\n'
        '    <img src="assets/header-writing-light.svg" alt="~/writing">\n'
        '  </picture>\n'
        '</h2>'
    )
    cells = [
        f'  <a href="{esc(link(post, i))}">\n'
        f'    <picture>\n'
        f'      <source media="(prefers-color-scheme: dark)" srcset="assets/{filename(i, "dark")}">\n'
        f'      <img src="assets/{filename(i, "light")}" width="{W}" alt="{esc(alt_text(post))}">\n'
        f'    </picture>\n'
        f'  </a>'
        for i, post in enumerate(posts, start=1)
    ]
    rows = ["\n".join(cells[i:i + 2]) for i in range(0, len(cells), 2)]
    more = (
        '<p align="center">\n'
        f'  <a href="https://{SITE}/blog?{esc(UTM)}&amp;utm_content=all-posts">All posts →</a>'
        f' · <a href="{FEED_URL}">RSS</a>\n'
        '</p>'
    )
    return "\n".join([heading, *(f'<p align="center">\n{row}\n</p>' for row in rows), more])
