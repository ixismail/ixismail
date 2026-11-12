"""Minimal GitHub API client with retries. Any token that can read public profiles works."""
from __future__ import annotations

import http.client
import json
import time
import urllib.request
from typing import Any

from profilegen.config import LOGIN

API = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


class GitHub:
    def __init__(self, token: str, *, attempts: int = 3, timeout: float = 20.0) -> None:
        self._headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": f"{LOGIN}-profile-readme",
        }
        self._attempts = attempts
        self._timeout = timeout

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        body = self._send(urllib.request.Request(
            f"{API}/graphql",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={**self._headers, "Content-Type": "application/json"},
        ))
        if body.get("errors"):
            raise GitHubError(f"GitHub returned errors: {body['errors']}")
        data: dict[str, Any] = body["data"]
        return data

    def rest(self, path: str) -> dict[str, Any]:
        return self._send(urllib.request.Request(
            f"{API}{path}", headers={**self._headers, "Accept": "application/vnd.github+json"},
        ))

    def _send(self, request: urllib.request.Request) -> dict[str, Any]:
        for attempt in range(1, self._attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    body: dict[str, Any] = json.load(response)
                    return body
            except (OSError, http.client.HTTPException) as error:
                if attempt == self._attempts:
                    raise GitHubError(f"Couldn't reach GitHub ({request.full_url}): {error}") from error
                time.sleep(2 * attempt)
        raise AssertionError("unreachable")
