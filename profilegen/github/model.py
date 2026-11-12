"""The data the live cards draw from."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Calendar:
    """One entry per day, oldest first; GitHub pads the first week back to a Sunday."""
    total: int
    first: date
    first_weekday: int  # 0 = Sunday
    dates: tuple[str, ...]
    counts: tuple[int, ...]
    levels: tuple[int, ...]  # 0..4


@dataclass(frozen=True)
class Week:
    commits: int
    pull_requests: int
    days: tuple[tuple[date, int], ...]


@dataclass(frozen=True)
class Year:
    """The last 365 days."""
    today: date
    active: int
    days: int
    longest: int
    longest_span: tuple[int, int]  # first and last index into `daily`
    current: int
    daily: tuple[int, ...]
    months: tuple[int, ...]  # the last 12 calendar months
    best_month: tuple[str, int]  # ("Jun 2026", 289)
    repos_this_year: int


@dataclass(frozen=True)
class Repo:
    name: str
    description: str
    url: str
    stars: int
    forks: int
    language: str | None
    color: str


@dataclass(frozen=True)
class Profile:
    calendar: Calendar
    week: Week
    year: Year
    languages: tuple[tuple[str, float], ...]  # (name, share of code)
    pinned: tuple[Repo, ...]
    commits: tuple[datetime, ...]  # local time, naive
