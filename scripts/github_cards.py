"""Generate the README's live GitHub cards, light and dark: the pinned repositories, the
activity tiles and the commit clock.

- Pinned repos: one card per repository pinned on the profile (pin and unpin on GitHub to
  change them), each its own image linking to its repo. The README's block between
  `<!-- pinned:start -->` and `<!-- pinned:end -->` is rewritten to match, and cards beyond the
  current count are deleted.
- Activity: tiles under the contributions card. The last 12 months (active days, the longest
  streak, the busiest month, public repos started this year), the last 7 days (commits, a bar
  per day) and the languages across the public repositories, by code size. Per-repository
  numbers only cover public repos, so the languages are deliberately not "this week's".

Usage:
  GH_TOKEN=... python scripts/github_cards.py

Stdlib only. The scheduled workflow (.github/workflows/update-profile.yml) runs it every day.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import github_api

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

QUERY = """query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { name description url stargazerCount forkCount
        primaryLanguage { name color } } }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: { field: CREATED_AT, direction: DESC }) {
      nodes { name createdAt
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
          edges { size node { name color } } } }
    }
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions totalPullRequestContributions
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
    year: contributionsCollection {
      contributionCalendar { totalContributions
        weeks { contributionDays { date contributionCount } } }
    }
  }
}"""

# Repos that aren't projects: the profile itself (its generator scripts and data) and the
# package-manager taps (they ship nukeport); the language stats skip them.
NOT_PROJECTS = {"ixismail", "scoop-bucket", "homebrew-tap"}
# Where the commit clock reads the hour: the commits' own offsets, shown in local time.
LOCAL_OFFSET = timedelta(hours=5)  # Lahore, UTC+5

MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# The README's palette: GitHub's own page colours, the name's amber, the link blue. The activity
# tiles keep colour for the data: numbers and labels wear text colours; the bars are neutral ink
# (the busiest in full ink); only the languages are hued. The tiles wear the contributions
# card's surface ("tile", "tile_line"), so the two read as one block.
THEMES = {
    "dark": {"card": "#0d1117", "line": "#30363d", "text": "#e6edf3", "muted": "#9198a1",
             "faint": "#6e7681", "accent": "#f59f1a", "link": "#58a6ff", "track": "#21262d",
             "bar": "#6e7681", "bar_strong": "#e6edf3",  # bars ≥ 3:1 on the card
             "tile": "rgba(255,255,255,0.02)", "tile_line": "rgba(255,255,255,0.1)",
             "rule": "rgba(255,255,255,0.08)", "trace": "rgba(255,255,255,0.07)",
             # Languages: categorical slots 1-3 stepped for the dark surface, then a grey "Other".
             # Validated all-pairs on #0d1117: CVD ΔE ≥ 9.4, normal ΔE ≥ 20.9, all ≥ 3:1.
             "series": ("#3987e5", "#d95926", "#199e70"), "other": "#6e7681"},
    "light": {"card": "#ffffff", "line": "#d0d7de", "text": "#1f2328", "muted": "#59636e",
              "faint": "#818b98", "accent": "#b4400c", "link": "#0969da", "track": "#eaeef2",
              "bar": "#818b98", "bar_strong": "#1f2328",  # bars ≥ 3:1 on the card
              "tile": "#ffffff", "tile_line": "rgba(0,0,0,0.1)",
              "rule": "rgba(0,0,0,0.08)", "trace": "rgba(0,0,0,0.07)",
              # Validated all-pairs on #ffffff: CVD ΔE ≥ 9.2, normal ΔE ≥ 24.0; the aqua is 2.8:1,
              # so every language is also named in the legend (never colour alone).
              "series": ("#2a78d6", "#eb6834", "#1baf7a"), "other": "#818b98"},
}

# The languages with a colour of their own, in a fixed order: a colour always means the same
# language, whatever this week's ranking. Everything else is "Other".
LANGUAGE_SLOTS = ("JavaScript", "Go", "TypeScript")

# Octicons (MIT), 16 x 16.
ICON_REPO = (
    "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 "
    "0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 "
    "1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 "
    ".25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
)
ICON_STAR = (
    "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 "
    "4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 "
    "6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 "
    "0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 "
    ".698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 "
    "1-.564-.41L8 2.694Z"
)
ICON_FORK = (
    "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 "
    "2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 "
    "6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 "
    "0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"
)


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def wrap(text: str, width: int, lines: int) -> list[str]:
    """Words into at most `lines` lines of at most `width` characters; when the text doesn't fit,
    the last line ends in an ellipsis."""
    out: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if len(candidate) <= width:
            line = candidate
            continue
        out.append(line)
        line = word
        if len(out) == lines:  # words left over: cut the last line short
            last = out[-1]
            while len(last) > width - 1 and " " in last:
                last = last.rsplit(" ", 1)[0]
            out[-1] = last.rstrip(",.;:-") + "…"
            return out
    if line:
        out.append(line)
    return out


# ---- Data ------------------------------------------------------------------------------------


def fetch(token: str) -> dict:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=6)
    data = github_api.graphql(token, QUERY, {
        "login": github_api.LOGIN,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    })["user"]

    pinned = [
        {
            "name": node["name"],
            "description": node["description"] or "",
            "url": node["url"],
            "stars": node["stargazerCount"],
            "forks": node["forkCount"],
            "language": (node["primaryLanguage"] or {}).get("name"),
            "color": (node["primaryLanguage"] or {}).get("color") or "#8b949e",
        }
        for node in data["pinnedItems"]["nodes"]
        if node  # a pinned gist or a repo the token can't see comes back empty
    ]

    sizes: dict[str, int] = {}
    for repo in data["repositories"]["nodes"]:
        # The profile repo's own generator scripts and data, and the package taps, aren't projects.
        if repo["name"] in NOT_PROJECTS:
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
    total = sum(sizes.values()) or 1
    languages = [(name, sizes[name] / total) for name in LANGUAGE_SLOTS if sizes.get(name)]
    rest = sum(size for name, size in sizes.items() if name not in LANGUAGE_SLOTS) / total
    if rest > 0:
        languages.append(("Other", rest))

    collection = data["contributionsCollection"]
    counts = {
        day["date"]: day["contributionCount"]
        for week in collection["contributionCalendar"]["weeks"]
        for day in week["contributionDays"]
    }
    days = [(start + timedelta(days=i), counts.get((start + timedelta(days=i)).isoformat(), 0))
            for i in range(7)]

    # The last 12 months: active days, the longest run of them, the busiest month.
    # Exactly the last 365 days (the calendar pads its first week back to a Sunday).
    since = (today - timedelta(days=364)).isoformat()
    year_days = [(d["date"], d["contributionCount"])
                 for week in data["year"]["contributionCalendar"]["weeks"]
                 for d in week["contributionDays"] if d["date"] >= since]
    # The longest run of active days (and where it sits), and the current one (today still
    # counts as part of it before its first contribution).
    longest = (0, 0, 0)  # length, first index, last index
    run_start = None
    for i, (_, count) in enumerate(year_days):
        if not count:
            run_start = None
            continue
        run_start = i if run_start is None else run_start
        if i - run_start + 1 > longest[0]:
            longest = (i - run_start + 1, run_start, i)
    current, i = 0, len(year_days) - 1
    if year_days and not year_days[i][1]:
        i -= 1
    while i >= 0 and year_days[i][1]:
        current, i = current + 1, i - 1
    months: dict[str, int] = {}
    for day, count in year_days:
        months[day[:7]] = months.get(day[:7], 0) + count
    best_month = max(months.items(), key=lambda item: (item[1], item[0]))

    repos = data["repositories"]["nodes"]
    return {
        "pinned": pinned,
        "languages": languages,
        "week": {
            "commits": collection["totalCommitContributions"],
            "pull_requests": collection["totalPullRequestContributions"],
            "days": days,
            "today": today,
        },
        "year": {
            "today": today,
            "total": data["year"]["contributionCalendar"]["totalContributions"],
            "active": sum(1 for _, count in year_days if count),
            "days": len(year_days),
            "longest": longest[0],
            "longest_span": longest[1:],
            "current": current,
            "daily": [count for _, count in year_days],
            "first": datetime.strptime(year_days[0][0], "%Y-%m-%d").date(),
            "months": [count for _, count in sorted(months.items())][-12:],
            "best_month": (datetime.strptime(best_month[0], "%Y-%m").strftime("%b %Y"), best_month[1]),
            "repos_this_year": sum(1 for repo in repos if repo["createdAt"].startswith(str(today.year))),
        },
        "commits": commit_times(token),
    }


def commit_times(token: str) -> list[datetime]:
    """When the newest public commits were made (up to 300, from the commit search), in local
    time. The search sees public repositories only."""
    times = []
    for page in (1, 2, 3):
        found = github_api.rest(
            token,
            f"/search/commits?q=author:{github_api.LOGIN}&sort=author-date&order=desc&per_page=100&page={page}",
        )
        for item in found["items"]:
            moment = datetime.fromisoformat(item["commit"]["author"]["date"].replace("Z", "+00:00"))
            times.append((moment.astimezone(timezone.utc) + LOCAL_OFFSET).replace(tzinfo=None))
        if len(found["items"]) < 100:
            break
    return times


# ---- Pinned repositories -----------------------------------------------------------------------

REPO_W, REPO_H = 410, 150


def repo_svg(repo: dict, t: dict) -> str:
    lines = wrap(repo["description"] or "No description yet.", 56, 2)
    description = "".join(
        f'<text x="20" y="{70 + i * 19}" font-family="{SANS}" font-size="12.5" fill="{t["muted"]}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    meta, x = [], 20
    if repo["language"]:
        meta.append(f'<circle cx="{x + 5}" cy="124" r="5" fill="{repo["color"]}"/>'
                    f'<text x="{x + 16}" y="128" font-family="{MONO}" font-size="11" fill="{t["muted"]}">{esc(repo["language"])}</text>')
        x += 16 + 7 * len(repo["language"]) + 18
    for icon, value in ((ICON_STAR, repo["stars"]), (ICON_FORK, repo["forks"])):
        meta.append(f'<path transform="translate({x} 117) scale(.875)" fill="{t["muted"]}" d="{icon}"/>'
                    f'<text x="{x + 19}" y="128" font-family="{MONO}" font-size="11" fill="{t["muted"]}">{value:,}</text>')
        x += 19 + 7 * len(f"{value:,}") + 18
    label = f'{repo["name"]}: {repo["description"]}'.rstrip(": ")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {REPO_W} {REPO_H}" width="{REPO_W}" height="{REPO_H}" role="img" aria-label="{esc(label)}">
<rect x=".5" y=".5" width="{REPO_W - 1}" height="{REPO_H - 1}" rx="12" fill="{t["card"]}" stroke="{t["line"]}"/>
<path transform="translate(20 22)" fill="{t["muted"]}" d="{ICON_REPO}"/>
<text x="44" y="35" font-family="{SANS}" font-size="15" font-weight="600" fill="{t["link"]}">{esc(repo["name"])}</text>
<path d="M{REPO_W - 30} 32L{REPO_W - 22} 24M{REPO_W - 28} 24H{REPO_W - 22}V30" fill="none" stroke="{t["muted"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
{description}
{"".join(meta)}
</svg>
'''


def readme_block(pinned: list[dict]) -> str:
    """Two cards a row; each its own image, linking to its repo."""
    cells = []
    for i, repo in enumerate(pinned, start=1):
        alt = esc(f'{repo["name"]}: {repo["description"]}'.rstrip(": "))
        cells.append(
            f'  <a href="{repo["url"]}">\n'
            f'    <picture>\n'
            f'      <source media="(prefers-color-scheme: dark)" srcset="assets/repo-{i}-dark.svg">\n'
            f'      <img src="assets/repo-{i}-light.svg" width="410" alt="{alt}">\n'
            f'    </picture>\n'
            f'  </a>'
        )
    rows = ["\n".join(cells[i:i + 2]) for i in range(0, len(cells), 2)]
    return "\n".join(f'<p align="center">\n{row}\n</p>' for row in rows)


def update_readme(pinned: list[dict]) -> None:
    text = README.read_text(encoding="utf-8")
    # Everything between the markers is replaced, whether the block is empty or not.
    pattern = re.compile(r"(<!-- pinned:start -->).*?(<!-- pinned:end -->)", re.S)
    if not pattern.search(text):
        sys.exit("README.md has no <!-- pinned:start --> / <!-- pinned:end --> block.")
    block = readme_block(pinned)
    updated = pattern.sub(lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}" if block else
                          f"{m.group(1)}\n{m.group(2)}", text)
    if updated != text:
        README.write_text(updated, encoding="utf-8", newline="\n")
        print("updated README.md (pinned repos)")


# ---- Activity: tiles under the contributions card ----------------------------------------------

# The contributions card's viewBox width, so at the same display width (820) the two share a scale.
TILES_W = 924
TILE_GAP = 12


def span(first, last) -> str:
    """Nov 6 – Nov 12, 2026 (one year shown once)."""
    if first.year == last.year:
        return f"{first:%b} {first.day} – {last:%b} {last.day}, {last.year}"
    return f"{first:%b} {first.day}, {first.year} – {last:%b} {last.day}, {last.year}"


def label(x, y, text, size, fill, weight=400, anchor="start", spacing=None) -> str:
    extra = f' text-anchor="{anchor}"' if anchor != "start" else ""
    extra += f' letter-spacing="{spacing}"' if spacing is not None else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}"{extra}>{esc(str(text))}</text>'


def tile(x, y, w, h, t) -> str:
    return f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" height="{h - 1:.1f}" rx="14" fill="{t["tile"]}" stroke="{t["tile_line"]}"/>'


def figure(x, y, value, caption, t, size=30) -> str:
    """A tile's figure in text ink, its caption muted underneath."""
    return label(x, y, value, size, t["text"], 800, spacing=-1) + label(x, y + 22, caption, 12, t["muted"])


def rounded_bar(x, base, w, h, fill, r=4.0) -> str:
    """A bar with rounded top corners, flat on the baseline."""
    r = min(r, h, w / 2)
    y = base - h
    return (f'<path d="M{x:.1f} {base:.1f}V{y + r:.1f}Q{x:.1f} {y:.1f} {x + r:.1f} {y:.1f}H{x + w - r:.1f}'
            f'Q{x + w:.1f} {y:.1f} {x + w:.1f} {y + r:.1f}V{base:.1f}Z" fill="{fill}"/>')


def rise(base: float, delay: float) -> str:
    """Wrap-ready: grow a bar up from the baseline once, on load (the finished bar without SMIL)."""
    return (f'<animateTransform attributeName="transform" type="scale" values="1 0;1 0;1 1" '
            f'keyTimes="0;{delay / (delay + 0.7):.3f};1" dur="{delay + 0.7:.2f}s" calcMode="spline" '
            f'keySplines="0 0 1 1;.3 0 .2 1" fill="freeze"/>')


def growing(base: float, delay: float, inner: str) -> str:
    return f'<g transform="translate(0 {base:.1f})"><g>{rise(base, delay)}<g transform="translate(0 {-base:.1f})">{inner}</g></g></g>'


def activity_svg(year: dict, week: dict, languages: list, t: dict) -> str:
    """Six tiles: four for the last 12 months, a wide one for this week, one for the languages."""
    import math

    g = TILE_GAP
    tw = (TILES_W - 3 * g) / 4
    row1 = 150
    out = []

    # Active days, with the share of the year as a ring.
    share = year["active"] / year["days"]
    out.append(tile(0, 0, tw, row1, t) + label(18, 30, "Active days", 12, t["muted"], 500)
               + figure(18, 78, year["active"], f'of the last {year["days"]}', t))
    cx, cy, r = tw - 48, 82, 28
    circ = 2 * math.pi * r
    out.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="none" stroke="{t["trace"]}" stroke-width="7"/>'
               f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="none" stroke="{t["bar_strong"]}" stroke-width="7" stroke-linecap="round" '
               f'stroke-dasharray="{circ * share:.1f} {circ:.1f}" transform="rotate(-90 {cx:.1f} {cy})">'
               f'<animate attributeName="stroke-dasharray" values="0 {circ:.1f};0 {circ:.1f};{circ * share:.1f} {circ:.1f}" '
               f'keyTimes="0;.2;1" dur="1.2s" calcMode="spline" keySplines="0 0 1 1;.3 0 .2 1" fill="freeze"/></circle>'
               + label(cx, cy + 4, f"{share * 100:.0f}%", 12, t["text"], 600, "middle"))

    # The longest streak, with every day of the year as a tick: active grey, idle blank, the
    # streak in full ink.
    x = tw + g
    digits = len(str(year["longest"]))
    out.append(tile(x, 0, tw, row1, t) + label(x + 18, 30, "Longest streak", 12, t["muted"], 500)
               + label(x + 18, 78, year["longest"], 30, t["text"], 800, spacing=-1)
               + label(x + 24 + 18.5 * digits, 78, "days", 14, t["muted"], 500)
               + label(x + 18, 100, f'current streak: {year["current"]} days', 12, t["muted"]))
    step = (tw - 36) / len(year["daily"])
    first, last = year["longest_span"]
    for i, count in enumerate(year["daily"]):
        fill = t["bar_strong"] if first <= i <= last else (t["bar"] if count else t["trace"])
        out.append(f'<rect x="{x + 18 + i * step:.2f}" y="120" width="{step * 0.6:.2f}" height="14" fill="{fill}"/>')

    # The busiest month, with the twelve months as small bars (the busiest in full ink).
    x = 2 * (tw + g)
    month, month_count = year["best_month"]
    out.append(tile(x, 0, tw, row1, t) + label(x + 18, 30, "Busiest month", 12, t["muted"], 500)
               + figure(x + 18, 78, month.split()[0], f"{month_count:,} contributions · {month.split()[1]}", t))
    top = max(year["months"]) or 1
    bw = (tw - 36 - 11 * 4) / len(year["months"])
    for i, count in enumerate(year["months"]):
        h = max(2.0, 22 * count / top)
        fill = t["bar_strong"] if count == top else t["bar"]
        out.append(growing(134, 0.3 + i * 0.04, rounded_bar(x + 18 + i * (bw + 4), 134, bw, h, fill, 1.5)))

    # Public repos started this year, one square each.
    x = 3 * (tw + g)
    repos = year["repos_this_year"]
    out.append(tile(x, 0, tw, row1, t) + label(x + 18, 30, "Repos started", 12, t["muted"], 500)
               + figure(x + 18, 78, repos, f'public, in {year["today"].year}', t))
    per_row = 14
    for i in range(repos):
        out.append(f'<rect x="{x + 18 + (i % per_row) * 13:.1f}" y="{122 - (repos - 1) // per_row * 13 + (i // per_row) * 13}" '
                   f'width="9" height="9" rx="2" fill="{t["bar"]}"/>')

    # This week: the commits, three small figures and a bar per day.
    y2, row2 = row1 + g, 214
    ww = 3 * tw + 2 * g
    days = week["days"]
    active = sum(1 for _, count in days if count)
    busiest_day, busiest = max(days, key=lambda d: (d[1], d[0]))
    out.append(tile(0, y2, ww, row2, t) + label(18, y2 + 30, "This week", 12, t["muted"], 500)
               + label(18, y2 + 48, span(days[0][0], days[-1][0]), 12, t["muted"])
               + label(18, y2 + 100, f'{week["commits"]:,}', 40, t["text"], 800, spacing=-1.5)
               + label(18, y2 + 122, "commits", 13, t["muted"], 500))
    small = [(f"{active}/7", "active days"),
             (busiest_day.strftime("%a") if busiest else "—", f"busiest · {busiest}" if busiest else "busiest"),
             (f'{week["pull_requests"]:,}', "pull requests")]
    for i, (value, caption) in enumerate(small):
        out.append(label(18 + i * 92, y2 + 170, value, 16, t["text"], 700) + label(18 + i * 92, y2 + 188, caption, 11, t["muted"]))
    out.append(f'<path d="M300.5 {y2 + 20}V{y2 + row2 - 20}" stroke="{t["rule"]}"/>')
    base, tall, bar_w = y2 + 172, 110, 30
    x0, width = 330, ww - 330 - 24
    gap = (width - 7 * bar_w) / 6
    most = max((count for _, count in days), default=0) or 1
    for i, (day, count) in enumerate(days):
        h = max(2.0, tall * count / most) if count else 2.0
        bx = x0 + i * (bar_w + gap)
        strong = count == busiest and count > 0
        out.append(growing(base, 0.15 + i * 0.05, rounded_bar(bx, base, bar_w, h, t["bar_strong"] if strong else t["bar"])))
        out.append(label(bx + bar_w / 2, base - h - 7, count, 11, t["text"] if strong else t["muted"], 600 if strong else 400, "middle"))
        out.append(label(bx + bar_w / 2, base + 18, day.strftime("%a"), 11, t["muted"], anchor="middle"))
    out.append(f'<path d="M{x0 - 6} {base + .5}H{x0 + width + 6}" stroke="{t["rule"]}"/>')

    # Languages: a row each (fixed colours, named, with a share-of-code bar), never colour alone.
    lx = ww + g
    colors = {name: t["series"][i] for i, name in enumerate(LANGUAGE_SLOTS)} | {"Other": t["other"]}
    inner = tw - 36
    out.append(tile(lx, y2, tw, row2, t) + label(lx + 18, y2 + 30, "Languages", 12, t["muted"], 500))
    for i, (name, share) in enumerate(languages):
        ly = y2 + 62 + i * 38
        out.append(f'<rect x="{lx + 18:.1f}" y="{ly - 9}" width="8" height="8" rx="2" fill="{colors[name]}"/>'
                   + label(lx + 32, ly, name, 12, t["text"]) + label(lx + tw - 18, ly, f"{share * 100:.1f}%", 12, t["muted"], anchor="end")
                   + f'<rect x="{lx + 18:.1f}" y="{ly + 8}" width="{inner:.1f}" height="4" rx="2" fill="{t["trace"]}"/>'
                   f'<rect x="{lx + 18:.1f}" y="{ly + 8}" width="{max(4, inner * share):.1f}" height="4" rx="2" fill="{colors[name]}"/>')

    h = y2 + row2
    summary = (f'The last 12 months: {year["active"]} of {year["days"]} days active; longest streak {year["longest"]} days '
               f'(current {year["current"]}); busiest month {month} with {month_count:,} contributions; '
               f'{repos} public repos started this year. This week, {span(days[0][0], days[-1][0])}: '
               f'{week["commits"]} commits, {active} of 7 days active, busiest {busiest_day.strftime("%A")} with {busiest}, '
               f'{week["pull_requests"]} pull requests. Languages across public repositories: '
               + ", ".join(f"{name} {share * 100:.1f}%" for name, share in languages) + ".")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TILES_W} {h}" width="{TILES_W}" height="{h}" '
            f'role="img" aria-label="{esc(summary)}" font-family="{SANS}">\n' + "\n".join(out) + "\n</svg>\n")


def clock_svg(times: list[datetime], t: dict) -> str:
    """When I commit, on a 24-hour dial: a bar per hour, longest at the busiest."""
    import math

    w, h, cx, cy, inner, outer = 410, 260, 112, 134, 30, 88
    hours = [0] * 24
    for moment in times:
        hours[moment.hour] += 1
    top = max(hours) or 1
    peak = max(range(24), key=lambda hr: hours[hr])
    bars = []
    for hr, count in enumerate(hours):
        angle = math.radians(hr * 15 - 90)
        length = inner + (outer - inner) * count / top if count else inner + 3
        x1, y1 = cx + inner * math.cos(angle), cy + inner * math.sin(angle)
        x2, y2 = cx + length * math.cos(angle), cy + length * math.sin(angle)
        strong = hr == peak
        bars.append(f'<path d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}" stroke="{t["accent"]}" stroke-opacity="{1 if strong else (0.5 if count else 0.15)}" stroke-width="9" stroke-linecap="round"/>')
    labels = "".join(
        f'<text x="{cx + (outer + 16) * math.cos(math.radians(hr * 15 - 90)):.1f}" y="{cy + (outer + 16) * math.sin(math.radians(hr * 15 - 90)) + 4:.1f}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{t["muted"]}">{hr:02d}</text>'
        for hr in (0, 6, 12, 18)
    )
    if 5 <= peak < 9:
        kind = "early bird"
    elif 9 <= peak < 12:
        kind = "morning coder"
    elif 12 <= peak < 17:
        kind = "afternoon coder"
    elif 17 <= peak < 21:
        kind = "evening coder"
    else:
        kind = "night owl"
    night = sum(hours[hr] for hr in (*range(21, 24), *range(0, 5)))
    share = round(100 * night / (sum(hours) or 1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="When I commit: mostly around {peak:02d}:00, a {kind}; {share}% after 9 pm.">
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["card"]}" stroke="{t["line"]}"/>
<circle cx="{cx}" cy="{cy}" r="{outer + 4}" fill="none" stroke="{t["line"]}" stroke-dasharray="2 5"/>
<g>{"".join(bars)}<animateTransform attributeName="transform" type="rotate" values="-20 {cx} {cy};0 {cx} {cy}" dur="1.2s" calcMode="spline" keySplines=".2 0 .2 1" fill="freeze"/></g>
{labels}
<text x="236" y="72" font-family="{MONO}" font-size="11" letter-spacing="2.5" fill="{t["muted"]}">WHEN I COMMIT</text>
<text x="236" y="112" font-family="{SANS}" font-size="24" font-weight="800" fill="{t["accent"]}">{peak:02d}:00</text>
<text x="236" y="132" font-family="{MONO}" font-size="11" fill="{t["muted"]}">busiest hour</text>
<text x="236" y="168" font-family="{SANS}" font-size="16" font-weight="700" fill="{t["text"]}">{kind}</text>
<text x="236" y="188" font-family="{MONO}" font-size="11" fill="{t["muted"]}">{share}% after 9 pm</text>
<text x="236" y="226" font-family="{MONO}" font-size="9.5" fill="{t["muted"]}">{len(times)} public commits · UTC+5</text>
</svg>
'''


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN (any token that can read public profiles).")
    data = fetch(token)
    ASSETS.mkdir(exist_ok=True)

    today = data["week"]["today"]
    for name, theme in THEMES.items():
        cards = {
            f"activity-{name}.svg": activity_svg(data["year"], data["week"], data["languages"], theme),
            f"clock-{name}.svg": clock_svg(data["commits"], theme),
        }
        for fname, svg in cards.items():
            (ASSETS / fname).write_text(svg, encoding="utf-8", newline="\n")
            print(f"wrote assets/{fname}")
        for i, repo in enumerate(data["pinned"], start=1):
            path = ASSETS / f"repo-{i}-{name}.svg"
            path.write_text(repo_svg(repo, theme), encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")
    # Cards for pins that are gone.
    for stale in ASSETS.glob("repo-*-*.svg"):
        number = int(stale.name.split("-")[1])
        if number > len(data["pinned"]):
            stale.unlink()
            print(f"removed {stale.relative_to(ROOT)}")
    update_readme(data["pinned"])


if __name__ == "__main__":
    main()
