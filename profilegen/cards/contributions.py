"""The 3D contributions card, ported from the portfolio's GitHub activity section
(components/home/github-activity, lib/github/calendar.ts) without its interactive parts."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from profilegen.config import LOGIN
from profilegen.github.model import Calendar
from profilegen.svg import EMOJI, SANS

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

CELL, GAP, ROWS, OFFSET_X, RADIUS, FONT = 12, 4, 7, 32, 2, 10
PITCH = CELL + GAP
MIN_LABEL_GAP_WEEKS = 2  # room for a 3-letter month label

PAD, SPACE, CARD_RADIUS = 24, 20, 16

# Projection: a weekday steps 5 px right and 5.4 px up, a week 1.9 px down.
DAY_X, DAY_Y, WEEK_Y = 5, -5.4, 1.9
FOOTPRINT, BARS_PADDING, LABEL_BAND, LABEL_OFFSET = 0.72, 8, 16, 14
MAX_HEIGHT, MIN_HEIGHT, EMPTY_HEIGHT = 100, 4, 2
OUTLIER_RATIO, KNEE_HEIGHT = 2.5, 82

# Octicons "mark-github" (MIT).
GITHUB_MARK = (
    "M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2"
    " 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12"
    " 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44"
    " 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51"
    " 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45"
    ".68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"
)


@dataclass(frozen=True)
class CardPalette:
    card: str
    card_stroke: str
    ink: str
    label: str
    month: str
    # Opaque, so back bars don't show through; front +18 % black, side +36 %.
    top: tuple[str, ...]
    front: tuple[str, ...]
    side: tuple[str, ...]


PALETTES = {
    "light": CardPalette(
        card="#ffffff", card_stroke="rgba(0,0,0,0.1)", ink="#000000", label="rgba(0,0,0,0.6)",
        month="rgba(0,0,0,0.6)",
        top=("#e5e7eb", "#9be9a8", "#40c463", "#30a14e", "#216e39"),
        front=("#bcbdc1", "#7fbf8a", "#34a151", "#278440", "#1b5a2f"),
        side=("#939496", "#63956c", "#297d3f", "#1f6732", "#154624"),
    ),
    "dark": CardPalette(
        card="rgba(255,255,255,0.02)", card_stroke="rgba(255,255,255,0.1)", ink="#ffffff",
        label="rgba(255,255,255,0.5)", month="rgba(255,255,255,0.55)",
        top=("#262626", "#0e4429", "#006d32", "#26a641", "#39d353"),
        front=("#1f1f1f", "#0b3822", "#005929", "#1f8835", "#2fad44"),
        side=("#181818", "#092c1a", "#004620", "#186a2a", "#248735"),
    ),
}

Point = tuple[float, float]


def week_count(cal: Calendar) -> int:
    return -(-(cal.first_weekday + len(cal.counts)) // ROWS)


def month_labels(cal: Calendar) -> list[tuple[str, int]]:
    """A label where the month changes, dropping any the next one crowds out."""
    candidates: list[tuple[str, int]] = []
    previous = -1
    for week in range(week_count(cal)):
        index = max(0, week * ROWS - cal.first_weekday)
        if index >= len(cal.counts):
            break
        month = (cal.first + timedelta(days=index)).month - 1
        if month != previous:
            candidates.append((MONTHS[month], week))
        previous = month
    return [
        label
        for i, label in enumerate(candidates)
        if i == len(candidates) - 1 or candidates[i + 1][1] - label[1] >= MIN_LABEL_GAP_WEEKS
    ]


def current_streak(counts: tuple[int, ...]) -> int:
    """Today at zero doesn't break the streak."""
    index = len(counts) - 1
    if index >= 0 and counts[index] == 0:
        index -= 1
    streak = 0
    while index >= 0 and counts[index] > 0:
        streak += 1
        index -= 1
    return streak


def height_scale(counts: tuple[int, ...]) -> Callable[[int], float]:
    """Linear 4-100 px; if the busiest day exceeds 2.5x the 98th percentile, up to that
    percentile maps to 4-82 px and the outliers to 82-100, so one day can't flatten the year."""
    active = sorted(c for c in counts if c > 0)
    if not active:
        return lambda count: EMPTY_HEIGHT
    top = active[-1]
    p98 = active[min(len(active) - 1, int(len(active) * 0.98))]
    guarded = p98 > 0 and top > OUTLIER_RATIO * p98

    def scale(count: int) -> float:
        if count <= 0:
            return EMPTY_HEIGHT
        c = min(count, top)
        if not guarded:
            return MIN_HEIGHT + (c / top) * (MAX_HEIGHT - MIN_HEIGHT)
        if c <= p98:
            return MIN_HEIGHT + (c / p98) * (KNEE_HEIGHT - MIN_HEIGHT)
        return KNEE_HEIGHT + ((c - p98) / (top - p98)) * (MAX_HEIGHT - KNEE_HEIGHT)

    return scale


@dataclass(frozen=True)
class Bar:
    level: int
    side: list[Point]
    front: list[Point]
    top: list[Point]


@dataclass(frozen=True)
class Layout:
    bars: list[Bar]  # painter's order
    months: list[tuple[str, float, float]]  # label, x, y
    height: int


def bars_layout(cal: Calendar) -> Layout:
    """One box per day. Day order is already back-to-front, so it is the painter's order."""
    weeks = week_count(cal)
    width = OFFSET_X + weeks * PITCH - GAP
    week_step = (width - BARS_PADDING * 2 - ROWS * DAY_X) / weeks
    scale = height_scale(cal.counts)
    heights = [scale(c) for c in cal.counts]

    def raw(x: float, y: float, z: float) -> Point:
        return x * week_step + y * DAY_X, x * WEEK_Y + y * DAY_Y - z

    points = [raw(0, 0, 0), raw(weeks, 0, 0), raw(0, ROWS, 0), raw(weeks, ROWS, 0)]
    inset = (1 - FOOTPRINT) / 2
    for index, h in enumerate(heights):
        slot = index + cal.first_weekday
        y = ROWS - 1 - (slot % ROWS) + inset + FOOTPRINT
        x = slot // ROWS + inset
        points += [raw(x, y, h), raw(x + FOOTPRINT, y, h)]
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    dx, dy = BARS_PADDING - min_x, BARS_PADDING - min_y

    def at(x: float, y: float, z: float) -> Point:
        px, py = raw(x, y, z)
        return round(px + dx, 1), round(py + dy, 1)

    bars = []
    for index, h in enumerate(heights):
        slot = index + cal.first_weekday
        week, row = slot // ROWS, ROWS - 1 - (slot % ROWS)
        x0, y0 = week + inset, row + inset
        x1, y1 = x0 + FOOTPRINT, y0 + FOOTPRINT
        bars.append(Bar(
            level=cal.levels[index],
            side=[at(x1, y0, 0), at(x1, y1, 0), at(x1, y1, h), at(x1, y0, h)],
            front=[at(x0, y0, 0), at(x1, y0, 0), at(x1, y0, h), at(x0, y0, h)],
            top=[at(x0, y0, h), at(x1, y0, h), at(x1, y1, h), at(x0, y1, h)],
        ))
    months = [
        (label, at(week + 0.5, 0, 0)[0], round(at(week + 0.5, 0, 0)[1] + LABEL_OFFSET, 1))
        for label, week in month_labels(cal)
    ]
    return Layout(bars=bars, months=months, height=int(-(-(max_y - min_y + BARS_PADDING * 2 + LABEL_BAND) // 1)))


def _quad(points: list[Point]) -> str:
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points) + "Z"


def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def _bars_markup(layout: Layout, p: CardPalette, grid_y: int) -> str:
    paths = "".join(
        f'<path fill="{p.side[b.level]}" d="{_quad(b.side)}"/>'
        f'<path fill="{p.front[b.level]}" d="{_quad(b.front)}"/>'
        f'<path fill="{p.top[b.level]}" d="{_quad(b.top)}"/>'
        for b in layout.bars
    )
    months = "".join(f'<text x="{x:g}" y="{y:g}" text-anchor="middle">{label}</text>' for label, x, y in layout.months)
    return (f'<g transform="translate({PAD} {grid_y})">{paths}'
            f'<g font-size="{FONT}" font-weight="500" fill="{p.month}">{months}</g></g>')


def render(cal: Calendar, theme: str) -> str:
    p = PALETTES[theme]
    streak, best_day = current_streak(cal.counts), max(cal.counts)
    width = PAD + OFFSET_X + week_count(cal) * PITCH - GAP + PAD
    grid_y = PAD + 44 + SPACE
    layout = bars_layout(cal)
    footer_y = grid_y + layout.height + SPACE + 8
    height = footer_y + 34 + PAD
    right = width - PAD

    def stat(x: int, icon: str, value: int, label: str) -> str:
        return (
            f'<text x="{x}" y="{footer_y + 23}" font-family="{EMOJI}" font-size="18">{icon}</text>'
            f'<text x="{x + 28}" y="{footer_y + 14}" font-size="14" font-weight="900" fill="{p.ink}">{value:,}</text>'
            f'<text x="{x + 28}" y="{footer_y + 28}" font-size="10" font-weight="500" letter-spacing="0.25" fill="{p.label}">{label}</text>'
        )

    stats = stat(PAD, "🔥", streak, "Day Streak")
    if best_day > 0:
        stats += stat(PAD + 110, "⚡", best_day, "Best Day")

    legend_cells = 5 * CELL + 4 * 6
    lx = right - 26 - 4 - legend_cells
    legend = [f'<text x="{lx - 4}" y="{footer_y + 21}" text-anchor="end" font-size="10" font-weight="500" fill="{p.label}">Less</text>']
    for level, fill in enumerate(p.top):
        legend.append(f'<rect x="{lx + level * (CELL + 6) + 0.5}" y="{footer_y + 11.5}" width="{CELL - 1}" height="{CELL - 1}" rx="{RADIUS}" fill="{fill}" stroke="none"/>')
    legend.append(f'<text x="{lx + legend_cells + 4}" y="{footer_y + 21}" font-size="10" font-weight="500" fill="{p.label}">More</text>')

    summary = (f"{cal.total:,} GitHub contributions in the last year by {LOGIN}. "
               f"Current streak {_plural(streak, 'day')}. Best day {_plural(best_day, 'contribution')}.")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{summary}" font-family="{SANS}">
<title>{summary}</title>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{CARD_RADIUS}" fill="{p.card}" stroke="{p.card_stroke}"/>
<svg x="{PAD}" y="{PAD + 9}" width="26" height="26" viewBox="0 0 16 16"><path fill="{p.ink}" d="{GITHUB_MARK}"/></svg>
<text x="{PAD + 34}" y="{PAD + 27}" font-size="14" font-weight="600" letter-spacing="-0.2" fill="{p.ink}">{LOGIN}</text>
<text x="{right}" y="{PAD + 22}" text-anchor="end" font-size="24" font-weight="900" letter-spacing="-1.2" fill="{p.ink}">{cal.total:,}</text>
<text x="{right}" y="{PAD + 40}" text-anchor="end" font-size="12" font-weight="500" fill="{p.label}">Contributions this year</text>
{_bars_markup(layout, p, grid_y)}
{stats}
{"".join(legend)}
</svg>
'''
