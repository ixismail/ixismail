"""One GraphQL query plus the commit search, fetched concurrently into a raw snapshot (which
can be saved and replayed offline), then parsed into a Profile."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from typing import Any

from profilegen.config import LANGUAGE_SLOTS, LOCAL_OFFSET, LOGIN, NOT_PROJECTS
from profilegen.github.client import GitHub, GitHubError
from profilegen.github.model import Calendar, Profile, Repo, Week, Year

QUERY = """query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { name description url stargazerCount forkCount
        primaryLanguage { name color } } }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: { field: CREATED_AT, direction: DESC }) {
      nodes { name createdAt
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) { edges { size node { name } } } }
    }
    week: contributionsCollection(from: $from, to: $to) {
      totalCommitContributions totalPullRequestContributions
    }
    year: contributionsCollection {
      contributionCalendar { totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } } }
    }
  }
}"""

LEVELS = ("NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE")
COMMIT_PAGES, PAGE_SIZE = 3, 100
UNKNOWN_LANGUAGE_COLOR = "#8b949e"


def fetch(client: GitHub, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    start = now.date() - timedelta(days=6)
    variables = {
        "login": LOGIN,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    search = (f"/search/commits?q=author:{LOGIN}&sort=author-date&order=desc"
              f"&per_page={PAGE_SIZE}&page={{page}}")
    with ThreadPoolExecutor(max_workers=1 + COMMIT_PAGES) as pool:
        user = pool.submit(client.graphql, QUERY, variables)
        pages = [pool.submit(client.rest, search.format(page=page)) for page in range(1, COMMIT_PAGES + 1)]
        commit_dates: list[str] = []
        for page in pages:
            items = page.result()["items"]
            commit_dates += [item["commit"]["author"]["date"] for item in items]
            if len(items) < PAGE_SIZE:
                break
        return {"fetched_at": now.isoformat(), "user": user.result()["user"], "commit_dates": commit_dates}


def parse(raw: dict[str, Any]) -> Profile:
    user = raw["user"]
    today = datetime.fromisoformat(raw["fetched_at"]).astimezone(timezone.utc).date()
    calendar = _calendar(user["year"]["contributionCalendar"])
    return Profile(
        calendar=calendar,
        week=_week(user["week"], calendar, today),
        year=_year(calendar, user["repositories"]["nodes"], today),
        languages=_languages(user["repositories"]["nodes"]),
        pinned=_pinned(user["pinnedItems"]["nodes"]),
        commits=_commit_times(raw["commit_dates"]),
    )


def _calendar(raw: dict[str, Any]) -> Calendar:
    days = [day for week in raw["weeks"] for day in week["contributionDays"]]
    if not days:
        raise GitHubError("The contribution calendar is empty.")
    # The grid layout depends on contiguous dates with matching weekdays.
    first = date.fromisoformat(days[0]["date"])
    for index, day in enumerate(days):
        expected = first + timedelta(days=index)
        if date.fromisoformat(day["date"]) != expected or day["weekday"] != expected.isoweekday() % 7:
            raise GitHubError(f"Unexpected calendar shape at {day['date']}.")
        if day["contributionLevel"] not in LEVELS:
            raise GitHubError(f"Unknown contribution level {day['contributionLevel']}.")
    return Calendar(
        total=raw["totalContributions"],
        first=first,
        first_weekday=days[0]["weekday"],
        dates=tuple(day["date"] for day in days),
        counts=tuple(day["contributionCount"] for day in days),
        levels=tuple(LEVELS.index(day["contributionLevel"]) for day in days),
    )


def _week(raw: dict[str, Any], calendar: Calendar, today: date) -> Week:
    counts = dict(zip(calendar.dates, calendar.counts))
    start = today - timedelta(days=6)
    days = tuple((day, counts.get(day.isoformat(), 0)) for day in (start + timedelta(days=i) for i in range(7)))
    return Week(commits=raw["totalCommitContributions"], pull_requests=raw["totalPullRequestContributions"], days=days)


def _year(calendar: Calendar, repos: list[dict[str, Any]], today: date) -> Year:
    since = (today - timedelta(days=364)).isoformat()
    days = [(day, count) for day, count in zip(calendar.dates, calendar.counts) if day >= since]
    daily = tuple(count for _, count in days)

    longest, span = 0, (0, 0)
    run_start: int | None = None
    for i, count in enumerate(daily):
        if not count:
            run_start = None
            continue
        run_start = i if run_start is None else run_start
        if i - run_start + 1 > longest:
            longest, span = i - run_start + 1, (run_start, i)

    # Today at zero doesn't break the current run.
    current, i = 0, len(daily) - 1
    if daily and not daily[i]:
        i -= 1
    while i >= 0 and daily[i]:
        current, i = current + 1, i - 1

    months: dict[str, int] = {}
    for day, count in days:
        months[day[:7]] = months.get(day[:7], 0) + count
    best, best_count = max(months.items(), key=lambda item: (item[1], item[0]))

    return Year(
        today=today,
        active=sum(1 for count in daily if count),
        days=len(daily),
        longest=longest,
        longest_span=span,
        current=current,
        daily=daily,
        months=tuple(count for _, count in sorted(months.items()))[-12:],
        best_month=(datetime.strptime(best, "%Y-%m").strftime("%b %Y"), best_count),
        repos_this_year=sum(1 for repo in repos if repo["createdAt"].startswith(str(today.year))),
    )


def _languages(repos: list[dict[str, Any]]) -> tuple[tuple[str, float], ...]:
    sizes: dict[str, int] = {}
    for repo in repos:
        if repo["name"] in NOT_PROJECTS:
            continue
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] = sizes.get(edge["node"]["name"], 0) + edge["size"]
    total = sum(sizes.values()) or 1
    shares = [(name, sizes[name] / total) for name in LANGUAGE_SLOTS if sizes.get(name)]
    rest = sum(size for name, size in sizes.items() if name not in LANGUAGE_SLOTS) / total
    if rest > 0:
        shares.append(("Other", rest))
    return tuple(shares)


def _pinned(nodes: list[dict[str, Any] | None]) -> tuple[Repo, ...]:
    return tuple(
        Repo(
            name=node["name"],
            description=node["description"] or "",
            url=node["url"],
            stars=node["stargazerCount"],
            forks=node["forkCount"],
            language=(node["primaryLanguage"] or {}).get("name"),
            color=(node["primaryLanguage"] or {}).get("color") or UNKNOWN_LANGUAGE_COLOR,
        )
        for node in nodes
        if node  # pinned gists come back empty
    )


def _commit_times(stamps: list[str]) -> tuple[datetime, ...]:
    return tuple(
        (datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc) + LOCAL_OFFSET).replace(tzinfo=None)
        for stamp in stamps
    )
