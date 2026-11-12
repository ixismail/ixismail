"""python -m profilegen {static,live,all,portrait-dots} [--record FILE] [--fixture FILE]

static: images that need no network. live: GitHub-driven images and the pinned block (needs
GH_TOKEN). --record saves the GitHub snapshot; --fixture renders from one offline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from profilegen import build
from profilegen.cards import portrait
from profilegen.github import GitHub, GitHubError, Profile, fetch, parse


def _profile(args: argparse.Namespace) -> Profile:
    if args.fixture:
        raw = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("Set GH_TOKEN (any token that can read public profiles), or pass --fixture.")
        raw = fetch(GitHub(token))
    if args.record:
        args.record.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    return parse(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m profilegen", description="Draw the profile README's images.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("static", help="images drawn from the repo alone")
    for command in ("live", "all"):
        sub = commands.add_parser(command, help="images drawn from GitHub data" + (" and the static ones" if command == "all" else ""))
        sub.add_argument("--fixture", type=Path, help="render from a saved snapshot instead of fetching")
        sub.add_argument("--record", type=Path, help="also save the raw snapshot here")
    commands.add_parser("portrait-dots", help="draw the portrait's dots (step 1 of the portrait)")
    args = parser.parse_args(argv)

    if args.command == "portrait-dots":
        portrait.DOTS.write_text(portrait.build_dots(), encoding="utf-8", newline="\n")
        print(f"wrote {portrait.DOTS}; rasterise it to {portrait.RASTER} (see profilegen/cards/portrait.py)")
        return 0

    report = build.Report()
    try:
        if args.command in ("live", "all"):
            profile = _profile(args)  # parse fully before writing anything
            build.write_assets(build.live_assets(profile), report)
            build.sync_pinned(profile, report)
        if args.command in ("static", "all"):
            build.write_assets(build.static_assets(), report)
    except (GitHubError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
