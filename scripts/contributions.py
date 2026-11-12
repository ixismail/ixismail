"""Generate the README's GitHub contributions card, light and dark.

The same card as the portfolio's GitHub activity section (themuhammadismail.com), drawn as a
static SVG: the GitHub mark and login, the year's total, the year's contributions, the current
streak, the best day and the Less / More legend. The README shows the 3D view (one bar per
day); the flat 2D grid can be drawn too (`--view 2d`). The geometry, colours and maths are the
portfolio's (`components/home/github-activity/geometry.ts`, `bars/geometry.ts`,
`bars/palette.ts`, `lib/github/calendar.ts`); only the interactive parts (the switch, the
tooltips) are left out: a README can't run scripts.

Usage:
  GH_TOKEN=... python scripts/contributions.py            (fetches the last year from GitHub)
  python scripts/contributions.py --fixture calendar.json  (renders a saved GraphQL response)
  python scripts/contributions.py --view 2d                (the flat grid instead)

Stdlib only. Writes assets/contributions-3d-{light,dark}.svg (or contributions-{light,dark}.svg
for 2D). The scheduled workflow (.github/workflows/update-profile.yml) runs it every day.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGIN = "ixismail"
QUERY = """query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}"""
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# The portfolio's geometry (geometry.ts).
CELL, GAP, ROWS, OFFSET_X, BAND, FONT, RADIUS = 12, 4, 7, 32, 16, 10, 2
PITCH = CELL + GAP
GRID_HEIGHT = BAND + ROWS * PITCH - GAP
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]
MIN_LABEL_GAP_WEEKS = 2  # a 3-letter label needs two columns of room

# The card around it (contribution-card.tsx): p-6, space-y-5, rounded-2xl.
PAD, SPACE, CARD_RADIUS = 24, 20, 16
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
EMOJI = "'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif"

# GitHub's mark (Octicons "mark-github", MIT), 16 x 16.
GITHUB_MARK = (
    "M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2"
    " 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12"
    " 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44"
    " 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51"
    " 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45"
    ".68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"
)

THEMES = {
    # contribution-card.tsx / geometry.ts, light and dark.
    "light": {
        "card": "#ffffff",
        "card_stroke": "rgba(0,0,0,0.1)",
        "ink": "#000000",
        "label": "rgba(0,0,0,0.6)",
        "month_label": "rgba(0,0,0,0.6)",
        "day_label": "rgba(0,0,0,0.6)",
        "levels": [
            ("rgba(0,0,0,0.05)", "rgba(0,0,0,0.05)"),
            ("rgba(16,185,129,0.2)", "rgba(16,185,129,0.3)"),
            ("rgba(16,185,129,0.4)", "rgba(16,185,129,0.5)"),
            ("rgba(16,185,129,0.7)", "rgba(16,185,129,0.7)"),
            ("rgb(52,211,153)", "rgb(52,211,153)"),
        ],
    },
    "dark": {
        "card": "rgba(255,255,255,0.02)",
        "card_stroke": "rgba(255,255,255,0.1)",
        "ink": "#ffffff",
        "label": "rgba(255,255,255,0.5)",
        "month_label": "rgba(255,255,255,0.6)",
        "day_label": "rgba(255,255,255,0.5)",
        "levels": [
            ("rgba(255,255,255,0.03)", "rgba(255,255,255,0.05)"),
            ("rgba(16,185,129,0.2)", "rgba(16,185,129,0.3)"),
            ("rgba(16,185,129,0.4)", "rgba(16,185,129,0.5)"),
            ("rgba(16,185,129,0.7)", "rgba(16,185,129,0.7)"),
            ("rgb(52,211,153)", "rgb(52,211,153)"),
        ],
    },
}


# ---- Data ------------------------------------------------------------------------------------


def fetch(token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-readme",
        },
    )
    # GitHub's API drops a connection now and then: three tries, a short pause between them.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except (OSError, http.client.HTTPException) as error:
            if attempt == 2:
                raise SystemExit(f"Couldn't reach GitHub: {error}") from error
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def calendar_of(response: dict) -> dict:
    """The GraphQL response → the portfolio's calendar model (calendar.ts's toCalendar)."""
    if response.get("errors"):
        raise SystemExit(f"GitHub returned errors: {response['errors']}")
    raw = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day for week in raw["weeks"] for day in week["contributionDays"]]
    if not days:
        raise SystemExit("The calendar is empty.")
    # Contiguous dates with matching weekdays, or the grid would be drawn wrong.
    first = date.fromisoformat(days[0]["date"])
    for index, day in enumerate(days):
        expected = first + timedelta(days=index)
        if date.fromisoformat(day["date"]) != expected or day["weekday"] != (expected.isoweekday() % 7):
            raise SystemExit(f"Unexpected calendar shape at {day['date']}.")
        if day["contributionLevel"] not in LEVELS:
            raise SystemExit(f"Unknown contribution level {day['contributionLevel']}.")

    counts = [day["contributionCount"] for day in days]
    first_weekday = days[0]["weekday"]
    weeks = -(-(first_weekday + len(days)) // ROWS)
    return {
        "total": raw["totalContributions"],
        "counts": counts,
        "first_weekday": first_weekday,
        "levels": [LEVELS.index(day["contributionLevel"]) for day in days],
        "weeks": weeks,
        "month_labels": month_labels(first, first_weekday, len(days), weeks),
        "streak": current_streak(counts),
        "best_day": max(counts),
    }


def month_labels(first: date, first_weekday: int, count: int, weeks: int) -> list[tuple[str, int]]:
    """One label per column where the month changes; drop one the next crowds out."""
    candidates: list[tuple[str, int]] = []
    previous = -1
    for week in range(weeks):
        index = max(0, week * ROWS - first_weekday)
        if index >= count:
            break
        month = (first + timedelta(days=index)).month - 1
        if month != previous:
            candidates.append((MONTHS[month], week))
        previous = month
    return [
        label
        for i, label in enumerate(candidates)
        if i == len(candidates) - 1 or candidates[i + 1][1] - label[1] >= MIN_LABEL_GAP_WEEKS
    ]


# ---- The 3D view (bars/geometry.ts, bars/palette.ts) -------------------------------------------

# GitHub's green ramp, opaque (translucent tops would let back bars show through front ones);
# the front face mixed with 18 % black, the side with 36 %.
BARS = {
    "light": {
        "top": ["#e5e7eb", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "front": ["#bcbdc1", "#7fbf8a", "#34a151", "#278440", "#1b5a2f"],
        "side": ["#939496", "#63956c", "#297d3f", "#1f6732", "#154624"],
        "month": "rgba(0,0,0,0.6)",
    },
    "dark": {
        "top": ["#262626", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "front": ["#1f1f1f", "#0b3822", "#005929", "#1f8835", "#2fad44"],
        "side": ["#181818", "#092c1a", "#004620", "#186a2a", "#248735"],
        "month": "rgba(255,255,255,0.55)",
    },
}
# A weekday is 5 px right and 5.4 px up; a week 1.9 px down and as wide as makes the drawing
# exactly as wide as the flat grid.
DAY_X, DAY_Y, WEEK_Y = 5, -5.4, 1.9
FOOTPRINT, BARS_PADDING, LABEL_BAND, LABEL_OFFSET = 0.72, 8, 16, 14
MAX_HEIGHT, MIN_HEIGHT, EMPTY_HEIGHT = 100, 4, 2
OUTLIER_RATIO, KNEE_HEIGHT = 2.5, 82


def height_scale(counts: list[int]):
    """Linear in 4–100 px, unless one outlier would flatten the year (the busiest day above
    2.5 × the 98th percentile): then up to that percentile in 4–82 px, the rest in 82–100."""
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


def bars_layout(cal: dict) -> dict:
    """One box per day: weeks running down-right, weekdays stepping back up-right. Bars come in
    the painter's order: week by week, back to front inside each (the nearer one is drawn last)."""
    width = OFFSET_X + cal["weeks"] * PITCH - GAP
    week_step = (width - BARS_PADDING * 2 - ROWS * DAY_X) / cal["weeks"]
    scale = height_scale(cal["counts"])
    heights = [scale(c) for c in cal["counts"]]

    def raw(x: float, y: float, z: float) -> tuple[float, float]:
        return x * week_step + y * DAY_X, x * WEEK_Y + y * DAY_Y - z

    points = [raw(0, 0, 0), raw(cal["weeks"], 0, 0), raw(0, ROWS, 0), raw(cal["weeks"], ROWS, 0)]
    inset = (1 - FOOTPRINT) / 2
    for index, h in enumerate(heights):
        slot = index + cal["first_weekday"]
        y = ROWS - 1 - (slot % ROWS) + inset + FOOTPRINT  # the top's back edge
        x = slot // ROWS + inset
        points += [raw(x, y, h), raw(x + FOOTPRINT, y, h)]
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    dx, dy = BARS_PADDING - min_x, BARS_PADDING - min_y

    def at(x: float, y: float, z: float) -> tuple[float, float]:
        px, py = raw(x, y, z)
        return round(px + dx, 1), round(py + dy, 1)

    bars = []
    for index, h in enumerate(heights):
        slot = index + cal["first_weekday"]
        week, y = slot // ROWS, ROWS - 1 - (slot % ROWS)
        x0, y0 = week + inset, y + inset
        x1, y1 = x0 + FOOTPRINT, y0 + FOOTPRINT
        bars.append(
            {
                "level": cal["levels"][index],
                # Drawn side, front, top: the top covers the others' shared edges.
                "side": [at(x1, y0, 0), at(x1, y1, 0), at(x1, y1, h), at(x1, y0, h)],
                "front": [at(x0, y0, 0), at(x1, y0, 0), at(x1, y0, h), at(x0, y0, h)],
                "top": [at(x0, y0, h), at(x1, y0, h), at(x1, y1, h), at(x0, y1, h)],
            }
        )
    # Slots run down each column (Sunday, the back row, first), so day order is already the
    # painter's order inside a week, and weeks follow one another.
    months = [
        (label, at(week + 0.5, 0, 0)[0], round(at(week + 0.5, 0, 0)[1] + LABEL_OFFSET, 1))
        for label, week in cal["month_labels"]
    ]
    return {
        "bars": bars,
        "months": months,
        "height": int(-(-(max_y - min_y + BARS_PADDING * 2 + LABEL_BAND) // 1)),
    }


def quad(points: list[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points) + "Z"


def current_streak(counts: list[int]) -> int:
    """Back from the last day; today still at zero isn't a break (the day isn't over)."""
    index = len(counts) - 1
    if index >= 0 and counts[index] == 0:
        index -= 1
    streak = 0
    while index >= 0 and counts[index] > 0:
        streak += 1
        index -= 1
    return streak


# ---- Drawing -----------------------------------------------------------------------------------


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def grid_markup(cal: dict, t: dict, grid_y: int) -> str:
    """The flat heatmap: month and weekday labels, cells grouped by level (each colour once)."""
    groups = []
    for level, (fill, stroke) in enumerate(t["levels"]):
        rects = []
        for index, lv in enumerate(cal["levels"]):
            if lv != level:
                continue
            slot = index + cal["first_weekday"]
            x = PAD + OFFSET_X + (slot // ROWS) * PITCH
            y = grid_y + BAND + (slot % ROWS) * PITCH
            rects.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RADIUS}"/>')
        if rects:
            groups.append(f'<g fill="{fill}" stroke="{stroke}">{"".join(rects)}</g>')
    months = "".join(
        f'<text x="{PAD + OFFSET_X + week * PITCH}" y="{grid_y + FONT}">{label}</text>'
        for label, week in cal["month_labels"]
    )
    days = "".join(
        f'<text x="{PAD + OFFSET_X - GAP * 2}" y="{grid_y + BAND + row * PITCH + CELL / 2}">{label}</text>'
        for row, label in enumerate(DAY_LABELS)
        if label
    )
    return (
        f'<g font-size="{FONT}" font-weight="500" fill="{t["month_label"]}">{months}</g>'
        f'<g font-size="{FONT}" font-weight="500" fill="{t["day_label"]}" text-anchor="end" dominant-baseline="middle">{days}</g>'
        f'<g stroke-width="1">{"".join(groups)}</g>'
    )


def bars_markup(layout: dict, palette: dict, grid_y: int) -> str:
    """The 3D bars, in the painter's order, with the month labels along the front edge."""
    paths = "".join(
        f'<path fill="{palette["side"][b["level"]]}" d="{quad(b["side"])}"/>'
        f'<path fill="{palette["front"][b["level"]]}" d="{quad(b["front"])}"/>'
        f'<path fill="{palette["top"][b["level"]]}" d="{quad(b["top"])}"/>'
        for b in layout["bars"]
    )
    months = "".join(
        f'<text x="{x:g}" y="{y:g}" text-anchor="middle">{label}</text>'
        for label, x, y in layout["months"]
    )
    return (
        f'<g transform="translate({PAD} {grid_y})">{paths}'
        f'<g font-size="{FONT}" font-weight="500" fill="{palette["month"]}">{months}</g></g>'
    )


def card_svg(cal: dict, name: str, view: str) -> str:
    """The card in one theme (`light` / `dark`) and one view (`2d` / `3d`)."""
    t = THEMES[name]
    grid_w = OFFSET_X + cal["weeks"] * PITCH - GAP
    width = PAD + grid_w + PAD
    header_h = 44
    grid_y = PAD + header_h + SPACE
    if view == "3d":
        layout = bars_layout(cal)
        graph, graph_h = bars_markup(layout, BARS[name], grid_y), layout["height"]
        swatches = [(fill, "none") for fill in BARS[name]["top"]]
    else:
        graph, graph_h = grid_markup(cal, t, grid_y), GRID_HEIGHT
        swatches = t["levels"]
    footer_y = grid_y + graph_h + SPACE + 8
    footer_h = 34
    height = footer_y + footer_h + PAD
    right = width - PAD

    def stat(x: int, icon: str, value: int, label: str) -> str:
        return (
            f'<text x="{x}" y="{footer_y + 23}" font-family="{EMOJI}" font-size="18">{icon}</text>'
            f'<text x="{x + 28}" y="{footer_y + 14}" font-size="14" font-weight="900" fill="{t["ink"]}">{value:,}</text>'
            f'<text x="{x + 28}" y="{footer_y + 28}" font-size="10" font-weight="500" letter-spacing="0.25" fill="{t["label"]}">{label}</text>'
        )

    stats = stat(PAD, "🔥", cal["streak"], "Day Streak")
    if cal["best_day"] > 0:
        stats += stat(PAD + 110, "⚡", cal["best_day"], "Best Day")

    # Legend, right-aligned: Less ▢▢▢▢▢ More.
    legend_cells = 5 * CELL + 4 * 6
    more_w = 26
    lx = right - more_w - 4 - legend_cells
    legend = [
        f'<text x="{lx - 4}" y="{footer_y + 21}" text-anchor="end" font-size="10" font-weight="500" fill="{t["label"]}">Less</text>'
    ]
    for level, (fill, stroke) in enumerate(swatches):
        legend.append(
            f'<rect x="{lx + level * (CELL + 6) + 0.5}" y="{footer_y + 11.5}" width="{CELL - 1}" height="{CELL - 1}" rx="{RADIUS}" fill="{fill}" stroke="{stroke}"/>'
        )
    legend.append(
        f'<text x="{lx + legend_cells + 4}" y="{footer_y + 21}" font-size="10" font-weight="500" fill="{t["label"]}">More</text>'
    )

    summary = (
        f"{cal['total']:,} GitHub contributions in the last year by {LOGIN}. "
        f"Current streak {plural(cal['streak'], 'day')}. Best day {plural(cal['best_day'], 'contribution')}."
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{summary}" font-family="{SANS}">
<title>{summary}</title>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{CARD_RADIUS}" fill="{t["card"]}" stroke="{t["card_stroke"]}"/>
<svg x="{PAD}" y="{PAD + 9}" width="26" height="26" viewBox="0 0 16 16"><path fill="{t["ink"]}" d="{GITHUB_MARK}"/></svg>
<text x="{PAD + 34}" y="{PAD + 27}" font-size="14" font-weight="600" letter-spacing="-0.2" fill="{t["ink"]}">{LOGIN}</text>
<text x="{right}" y="{PAD + 22}" text-anchor="end" font-size="24" font-weight="900" letter-spacing="-1.2" fill="{t["ink"]}">{cal["total"]:,}</text>
<text x="{right}" y="{PAD + 40}" text-anchor="end" font-size="12" font-weight="500" fill="{t["label"]}">Contributions this year</text>
{graph}
{stats}
{"".join(legend)}
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", type=Path, help="a saved GraphQL response to render instead")
    parser.add_argument(
        "--view", choices=("3d", "2d"), default="3d", help="the 3D bars (the README's) or the flat grid"
    )
    args = parser.parse_args()

    if args.fixture:
        response = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GH_TOKEN (any token that can read public profiles), or pass --fixture.")
        response = fetch(token)

    cal = calendar_of(response)
    ASSETS.mkdir(exist_ok=True)
    suffix = "-3d" if args.view == "3d" else ""
    for name in THEMES:
        path = ASSETS / f"contributions{suffix}-{name}.svg"
        path.write_text(card_svg(cal, name, args.view), encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ASSETS.parent)}")
    print(f"{cal['total']:,} contributions, streak {cal['streak']}, best day {cal['best_day']}")


if __name__ == "__main__":
    main()
