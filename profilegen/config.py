"""Identity, settings and paths."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

LOGIN = "ixismail"
NAME = "Muhammad Ismail"
TAGLINE = "Full Stack Software Engineer"
SITE = "themuhammadismail.com"

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
