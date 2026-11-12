"""One GraphQL call to GitHub, shared by the scripts that draw the README's live cards.

Stdlib only. A token that can read public profiles is enough (the workflow's own, or a
fine-grained one with no extra permissions).
"""
from __future__ import annotations

import http.client
import json
import time
import urllib.request

LOGIN = "ixismail"


def rest(token: str, path: str) -> dict:
    """A GET on GitHub's REST API (for what GraphQL lacks, like the commit search), with the
    same three tries."""
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{LOGIN}-profile-readme",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except (OSError, http.client.HTTPException) as error:
            if attempt == 2:
                raise SystemExit(f"Couldn't reach GitHub: {error}") from error
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def graphql(token: str, query: str, variables: dict) -> dict:
    """The response's `data`. GitHub's API drops a connection now and then: three tries, a short
    pause between them; GraphQL errors stop the run (nothing half-drawn gets committed)."""
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-readme",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.load(response)
            break
        except (OSError, http.client.HTTPException) as error:
            if attempt == 2:
                raise SystemExit(f"Couldn't reach GitHub: {error}") from error
            time.sleep(2 * (attempt + 1))
    if body.get("errors"):
        raise SystemExit(f"GitHub returned errors: {body['errors']}")
    return body["data"]
