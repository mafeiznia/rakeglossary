"""Fetch the Persian Wikipedia title for an English term.

Uses the `langlinks` API on English Wikipedia to find the corresponding
Persian article title. This is a good fallback for translating proper
names (cities, people, organizations) that Argos often can't handle.

Example:
    fetch_persian_title("Kagoshima") -> "کاگوشیما"
    fetch_persian_title("Albert Einstein") -> "آلبرت اینشتین"
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("definitions.wiki_langlinks")

_HEADERS = {"User-Agent": settings.user_agent}
_API_URL = "https://en.wikipedia.org/w/api.php"


def fetch_persian_title(term: str) -> str | None:
    """Return the Persian Wikipedia title for `term`, or None.

    Uses the langlinks API which is fast and returns clean titles.
    """
    if not term or not term.strip():
        return None

    params: dict[str, str | int] = {
        "action": "query",
        "format": "json",
        "prop": "langlinks",
        "lllang": "fa",
        "redirects": 1,
        "titles": term.strip(),
    }

    try:
        with httpx.Client(timeout=settings.wikipedia_timeout, headers=_HEADERS) as client:
            response = client.get(_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        log.debug(f"langlinks HTTP error for '{term}': {exc}")
        return None
    except ValueError as exc:
        log.debug(f"langlinks invalid JSON for '{term}': {exc}")
        return None

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        langlinks = page.get("langlinks", [])
        if not langlinks:
            continue
        # First langlink matches the requested language
        title = (langlinks[0].get("*") or "").strip()
        if title:
            return title
    return None
