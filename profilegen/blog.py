"""The newest blog posts, read from the site's RSS feed (no token, no dependencies).

The feed is the site's own `/blog/feed.xml`: each item's title, link, date, category, excerpt and a
small cover (`media:thumbnail`, the cover's 640 px WebP). Covers are embedded in the cards (an SVG
shown as an <img> can't load outside images), so they're fetched here: https only, from the site's
own domains, of an image type, and capped in size.
"""
from __future__ import annotations

import http.client
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

from profilegen.config import BLOG_POSTS, COVER_MAX_BYTES, FEED_URL, LOGIN, SITE

MEDIA_NS = "{http://search.yahoo.com/mrss/}"
COVER_TYPES = {"image/webp", "image/jpeg", "image/png"}


class BlogError(RuntimeError):
    pass


@dataclass(frozen=True)
class Post:
    title: str
    url: str
    published: date
    category: str
    excerpt: str
    cover: bytes | None
    cover_mime: str | None


def _get(url: str, *, attempts: int = 3, timeout: float = 20.0, limit: int | None = None) -> tuple[bytes, str]:
    """GET `url`: its body (at most `limit` bytes, else BlogError) and its content type."""
    request = urllib.request.Request(url, headers={"User-Agent": f"{LOGIN}-profile-readme"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                kind = response.headers.get_content_type()
                body = response.read(limit + 1 if limit else -1)
                if limit and len(body) > limit:
                    raise BlogError(f"{url} is larger than {limit} bytes")
                return body, kind
        except (OSError, http.client.HTTPException) as error:
            if attempt == attempts:
                raise BlogError(f"Couldn't fetch {url}: {error}") from error
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def _own_https(url: str) -> bool:
    """An https address on the site or one of its subdomains (the media domain)."""
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and (host == SITE or host.endswith(f".{SITE}"))


def parse_feed(xml: bytes, limit: int = BLOG_POSTS) -> list[dict[str, str]]:
    """The newest `limit` items, as plain fields (the feed lists newest first)."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise BlogError(f"The feed isn't valid XML: {error}") from error
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise BlogError("The feed isn't RSS 2.0.")
    items = []
    for item in channel.findall("item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue
        thumbnail = item.find(f"{MEDIA_NS}thumbnail")
        items.append({
            "title": title,
            "url": link,
            "date": (item.findtext("pubDate") or "").strip(),
            "category": (item.findtext("category") or "").strip(),
            "excerpt": " ".join((item.findtext("description") or "").split()),
            "cover": thumbnail.get("url", "") if thumbnail is not None else "",
        })
    return items


def _cover(url: str, fixture_dir: Path | None) -> tuple[bytes | None, str | None]:
    """The cover's bytes and type, or (None, None) when it can't be used (the card draws a band)."""
    if not url:
        return None, None
    if fixture_dir is not None and not url.startswith("https://"):
        path = (fixture_dir / url).resolve()
        mime = {".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        kind = mime.get(path.suffix.lower())
        return (path.read_bytes(), kind) if kind and path.is_file() else (None, None)
    if not _own_https(url):
        return None, None
    try:
        body, kind = _get(url, limit=COVER_MAX_BYTES)
    except BlogError:
        return None, None
    return (body, kind) if kind in COVER_TYPES else (None, None)


def _published(raw: str) -> date:
    try:
        return parsedate_to_datetime(raw).date()
    except (TypeError, ValueError) as error:
        raise BlogError(f"A post has an unreadable date: {raw!r}") from error


def newest_posts(fixture: Path | None = None) -> list[Post]:
    """The newest posts, covers included, from the live feed or a saved one (`fixture`)."""
    xml = fixture.read_bytes() if fixture else _get(FEED_URL, limit=5_000_000)[0]
    posts = []
    for item in parse_feed(xml):
        cover, mime = _cover(item["cover"], fixture.parent if fixture else None)
        posts.append(Post(
            title=item["title"],
            url=item["url"],
            published=_published(item["date"]),
            category=item["category"],
            excerpt=item["excerpt"],
            cover=cover,
            cover_mime=mime,
        ))
    return posts
