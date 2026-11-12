"""Maps each card to its asset file and writes only what changed.

To add an image: add a card module, list its files below, and add its <picture> to README.md.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from profilegen import readme
from profilegen.cards import (achievements, activity, clock, contributions, cta, header, hero, name,
                              notes, portrait, repos, signoff, waves)
from profilegen.config import ASSETS
from profilegen.github.model import Profile
from profilegen.theme import THEMES

Asset = tuple[str, str]  # (file name, SVG)


def static_assets() -> Iterator[Asset]:
    yield "portrait-halftone.svg", portrait.render(card=False)
    yield "portrait-halftone-card.svg", portrait.render(card=True)
    yield "wave-top.svg", waves.render("top")
    yield "wave-bottom.svg", waves.render("bottom")
    for theme, t in THEMES.items():
        yield f"name-{theme}.svg", name.render(t)
        yield f"header-projects-{theme}.svg", header.render("projects", t)
        yield f"header-toolbox-{theme}.svg", header.render("toolbox", t)
        yield f"achievements-{theme}.svg", achievements.render(t)
        yield f"notes-{theme}.svg", notes.render(t)
        yield f"hero-{theme}.svg", hero.render(t)
        yield f"cta-{theme}.svg", cta.render(theme)
        yield f"thanks-{theme}.svg", signoff.thanks_svg(t)
        yield f"top-{theme}.svg", signoff.top_svg(t)


def live_assets(profile: Profile) -> Iterator[Asset]:
    for theme, t in THEMES.items():
        yield f"contributions-3d-{theme}.svg", contributions.render(profile.calendar, theme)
        yield f"activity-{theme}.svg", activity.render(profile.year, profile.week, profile.languages, t)
        yield f"clock-{theme}.svg", clock.render(profile.commits, t)
        for i, repo in enumerate(profile.pinned, start=1):
            yield repos.filename(i, theme), repos.render(repo, t)


@dataclass
class Report:
    written: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    readme: bool = False

    def __str__(self) -> str:
        lines = [f"wrote assets/{f}" for f in self.written] + [f"removed assets/{f}" for f in self.removed]
        if self.readme:
            lines.append("updated README.md (pinned repos)")
        lines.append(f"{len(self.written)} written, {len(self.unchanged)} unchanged, {len(self.removed)} removed")
        return "\n".join(lines)


def _write(path: Path, content: str) -> bool:
    """Write unless unchanged (ignoring CRLF); True if written."""
    if path.exists() and path.read_text(encoding="utf-8").replace("\r\n", "\n") == content:
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def write_assets(assets: Iterator[Asset], report: Report) -> None:
    ASSETS.mkdir(exist_ok=True)
    for filename, svg in assets:
        (report.written if _write(ASSETS / filename, svg) else report.unchanged).append(filename)


def sync_pinned(profile: Profile, report: Report) -> None:
    """Delete cards of unpinned repos and rewrite the README's pinned block."""
    for stale in sorted(ASSETS.glob("repo-*-*.svg")):
        if int(stale.name.split("-")[1]) > len(profile.pinned):
            stale.unlink()
            report.removed.append(stale.name)
    report.readme = readme.update_block("pinned", repos.readme_block(profile.pinned))
