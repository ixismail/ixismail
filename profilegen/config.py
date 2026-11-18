"""Identity, settings and paths."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

LOGIN = "ixismail"
NAME = "Muhammad Ismail"
TAGLINE = "Full Stack Software Engineer"
SITE = "themuhammadismail.com"

# The ~/writing section: the newest posts from the site's feed, two cards a row.
FEED_URL = f"https://{SITE}/blog/feed.xml"
BLOG_POSTS = 4
COVER_MAX_BYTES = 400_000  # a 640 px WebP cover is far smaller; anything bigger is refused

LOCAL_OFFSET = timedelta(hours=5)  # commit clock time zone (Lahore)
LOCAL_OFFSET_LABEL = "UTC+5"

# Excluded from language stats: this repo and nukeport's package taps.
NOT_PROJECTS = frozenset({"ixismail", "scoop-bucket", "homebrew-tap"})

# Languages with a fixed colour, in slot order; the rest become "Other".
LANGUAGE_SLOTS = ("JavaScript", "Go", "TypeScript")

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
ART = PACKAGE / "art"
