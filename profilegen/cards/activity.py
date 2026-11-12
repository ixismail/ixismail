"""The activity tiles: the last 12 months, this week, and languages by code size."""
from __future__ import annotations

import math
from datetime import date

from profilegen.config import LANGUAGE_SLOTS
from profilegen.github.model import Week, Year
from profilegen.svg import SANS, esc
from profilegen.theme import Palette

WIDTH = 924  # the contributions card's width, so both share a scale
GAP = 12
TILE_W = (WIDTH - 3 * GAP) / 4
ROW1_H, ROW2_H = 150, 214
INSET = 18


def span(first: date, last: date) -> str:
    """"Nov 6 – Nov 12, 2026"."""
    if first.year == last.year:
        return f"{first:%b} {first.day} – {last:%b} {last.day}, {last.year}"
    return f"{first:%b} {first.day}, {first.year} – {last:%b} {last.day}, {last.year}"


def label(x: float, y: float, text: object, size: float, fill: str, weight: int = 400,
          anchor: str = "start", spacing: float | None = None) -> str:
    extra = f' text-anchor="{anchor}"' if anchor != "start" else ""
    extra += f' letter-spacing="{spacing}"' if spacing is not None else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}"{extra}>{esc(str(text))}</text>'


def tile(x: float, y: float, w: float, h: float, t: Palette) -> str:
    return f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" height="{h - 1:.1f}" rx="14" fill="{t.tile}" stroke="{t.tile_line}"/>'


def figure(x: float, y: float, value: object, caption: str, t: Palette) -> str:
    return label(x, y, value, 30, t.text, 800, spacing=-1) + label(x, y + 22, caption, 12, t.muted)


def rounded_bar(x: float, base: float, w: float, h: float, fill: str, r: float = 4.0) -> str:
    r = min(r, h, w / 2)
    y = base - h
    return (f'<path d="M{x:.1f} {base:.1f}V{y + r:.1f}Q{x:.1f} {y:.1f} {x + r:.1f} {y:.1f}H{x + w - r:.1f}'
            f'Q{x + w:.1f} {y:.1f} {x + w:.1f} {y + r:.1f}V{base:.1f}Z" fill="{fill}"/>')


def growing(base: float, delay: float, inner: str) -> str:
    """Grow `inner` up from the baseline on load."""
    rise = (f'<animateTransform attributeName="transform" type="scale" values="1 0;1 0;1 1" '
            f'keyTimes="0;{delay / (delay + 0.7):.3f};1" dur="{delay + 0.7:.2f}s" calcMode="spline" '
            f'keySplines="0 0 1 1;.3 0 .2 1" fill="freeze"/>')
    return f'<g transform="translate(0 {base:.1f})"><g>{rise}<g transform="translate(0 {-base:.1f})">{inner}</g></g></g>'


def _active_days(year: Year, t: Palette) -> str:
    share = year.active / year.days
    cx, cy, r = TILE_W - 48, 82, 28
    circ = 2 * math.pi * r
    return (tile(0, 0, TILE_W, ROW1_H, t) + label(INSET, 30, "Active days", 12, t.muted, 500)
            + figure(INSET, 78, year.active, f"of the last {year.days}", t) + "\n"
            + f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="none" stroke="{t.trace}" stroke-width="7"/>'
            f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="none" stroke="{t.bar_strong}" stroke-width="7" stroke-linecap="round" '
            f'stroke-dasharray="{circ * share:.1f} {circ:.1f}" transform="rotate(-90 {cx:.1f} {cy})">'
            f'<animate attributeName="stroke-dasharray" values="0 {circ:.1f};0 {circ:.1f};{circ * share:.1f} {circ:.1f}" '
            f'keyTimes="0;.2;1" dur="1.2s" calcMode="spline" keySplines="0 0 1 1;.3 0 .2 1" fill="freeze"/></circle>'
            + label(cx, cy + 4, f"{share * 100:.0f}%", 12, t.text, 600, "middle"))


def _longest_streak(year: Year, t: Palette, x: float) -> str:
    """A tick per day of the year, the longest streak highlighted."""
    out = [tile(x, 0, TILE_W, ROW1_H, t) + label(x + INSET, 30, "Longest streak", 12, t.muted, 500)
           + label(x + INSET, 78, year.longest, 30, t.text, 800, spacing=-1)
           + label(x + 24 + 18.5 * len(str(year.longest)), 78, "days", 14, t.muted, 500)
           + label(x + INSET, 100, f"current streak: {year.current} days", 12, t.muted)]
    step = (TILE_W - 2 * INSET) / len(year.daily)
    first, last = year.longest_span
    for i, count in enumerate(year.daily):
        fill = t.bar_strong if first <= i <= last else (t.bar if count else t.trace)
        out.append(f'<rect x="{x + INSET + i * step:.2f}" y="120" width="{step * 0.6:.2f}" height="14" fill="{fill}"/>')
    return "\n".join(out)


def _busiest_month(year: Year, t: Palette, x: float) -> str:
    month, count = year.best_month
    name, yr = month.split()
    out = [tile(x, 0, TILE_W, ROW1_H, t) + label(x + INSET, 30, "Busiest month", 12, t.muted, 500)
           + figure(x + INSET, 78, name, f"{count:,} contributions · {yr}", t)]
    top = max(year.months) or 1
    bw = (TILE_W - 2 * INSET - 11 * 4) / len(year.months)
    for i, value in enumerate(year.months):
        h = max(2.0, 22 * value / top)
        fill = t.bar_strong if value == top else t.bar
        out.append(growing(134, 0.3 + i * 0.04, rounded_bar(x + INSET + i * (bw + 4), 134, bw, h, fill, 1.5)))
    return "\n".join(out)


def _repos_started(year: Year, t: Palette, x: float) -> str:
    repos, per_row = year.repos_this_year, 14
    out = [tile(x, 0, TILE_W, ROW1_H, t) + label(x + INSET, 30, "Repos started", 12, t.muted, 500)
           + figure(x + INSET, 78, repos, f"public, in {year.today.year}", t)]
    for i in range(repos):
        out.append(f'<rect x="{x + INSET + (i % per_row) * 13:.1f}" y="{122 - (repos - 1) // per_row * 13 + (i // per_row) * 13}" '
                   f'width="9" height="9" rx="2" fill="{t.bar}"/>')
    return "\n".join(out)


def _this_week(week: Week, t: Palette, y: float, w: float) -> str:
    days = week.days
    active = sum(1 for _, count in days if count)
    busiest_day, busiest = max(days, key=lambda d: (d[1], d[0]))
    out = [tile(0, y, w, ROW2_H, t) + label(INSET, y + 30, "This week", 12, t.muted, 500)
           + label(INSET, y + 48, span(days[0][0], days[-1][0]), 12, t.muted)
           + label(INSET, y + 100, f"{week.commits:,}", 40, t.text, 800, spacing=-1.5)
           + label(INSET, y + 122, "commits", 13, t.muted, 500)]
    small = [(f"{active}/7", "active days"),
             (busiest_day.strftime("%a") if busiest else "—", f"busiest · {busiest}" if busiest else "busiest"),
             (f"{week.pull_requests:,}", "pull requests")]
    for i, (value, caption) in enumerate(small):
        out.append(label(INSET + i * 92, y + 170, value, 16, t.text, 700) + label(INSET + i * 92, y + 188, caption, 11, t.muted))
    out.append(f'<path d="M300.5 {y + 20}V{y + ROW2_H - 20}" stroke="{t.rule}"/>')

    base, tall, bar_w = y + 172, 110, 30
    x0, width = 330, w - 330 - 24
    gap = (width - 7 * bar_w) / 6
    most = max((count for _, count in days), default=0) or 1
    for i, (day, count) in enumerate(days):
        h = max(2.0, tall * count / most) if count else 2.0
        bx = x0 + i * (bar_w + gap)
        strong = count == busiest and count > 0
        out.append(growing(base, 0.15 + i * 0.05, rounded_bar(bx, base, bar_w, h, t.bar_strong if strong else t.bar)))
        out.append(label(bx + bar_w / 2, base - h - 7, count, 11, t.text if strong else t.muted, 600 if strong else 400, "middle"))
        out.append(label(bx + bar_w / 2, base + 18, day.strftime("%a"), 11, t.muted, anchor="middle"))
    out.append(f'<path d="M{x0 - 6} {base + .5}H{x0 + width + 6}" stroke="{t.rule}"/>')
    return "\n".join(out)


def _languages(languages: tuple[tuple[str, float], ...], t: Palette, x: float, y: float) -> str:
    colors = {name: t.series[i] for i, name in enumerate(LANGUAGE_SLOTS)} | {"Other": t.other}
    inner = TILE_W - 2 * INSET
    out = [tile(x, y, TILE_W, ROW2_H, t) + label(x + INSET, y + 30, "Languages", 12, t.muted, 500)]
    for i, (name, share) in enumerate(languages):
        ly = y + 62 + i * 38
        out.append(f'<rect x="{x + INSET:.1f}" y="{ly - 9}" width="8" height="8" rx="2" fill="{colors[name]}"/>'
                   + label(x + 32, ly, name, 12, t.text) + label(x + TILE_W - INSET, ly, f"{share * 100:.1f}%", 12, t.muted, anchor="end")
                   + f'<rect x="{x + INSET:.1f}" y="{ly + 8}" width="{inner:.1f}" height="4" rx="2" fill="{t.trace}"/>'
                   f'<rect x="{x + INSET:.1f}" y="{ly + 8}" width="{max(4, inner * share):.1f}" height="4" rx="2" fill="{colors[name]}"/>')
    return "\n".join(out)


def _summary(year: Year, week: Week, languages: tuple[tuple[str, float], ...]) -> str:
    days = week.days
    active = sum(1 for _, count in days if count)
    busiest_day, busiest = max(days, key=lambda d: (d[1], d[0]))
    month, count = year.best_month
    return (f"The last 12 months: {year.active} of {year.days} days active; longest streak {year.longest} days "
            f"(current {year.current}); busiest month {month} with {count:,} contributions; "
            f"{year.repos_this_year} public repos started this year. This week, {span(days[0][0], days[-1][0])}: "
            f'{week.commits} commits, {active} of 7 days active, busiest {busiest_day.strftime("%A")} with {busiest}, '
            f"{week.pull_requests} pull requests. Languages across public repositories: "
            + ", ".join(f"{name} {share * 100:.1f}%" for name, share in languages) + ".")


def render(year: Year, week: Week, languages: tuple[tuple[str, float], ...], t: Palette) -> str:
    row2_y = ROW1_H + GAP
    wide = 3 * TILE_W + 2 * GAP
    tiles = [
        _active_days(year, t),
        _longest_streak(year, t, TILE_W + GAP),
        _busiest_month(year, t, 2 * (TILE_W + GAP)),
        _repos_started(year, t, 3 * (TILE_W + GAP)),
        _this_week(week, t, row2_y, wide),
        _languages(languages, t, wide + GAP, row2_y),
    ]
    height = row2_y + ROW2_H
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
            f'role="img" aria-label="{esc(_summary(year, week, languages))}" font-family="{SANS}">\n' + "\n".join(tiles) + "\n</svg>\n")
