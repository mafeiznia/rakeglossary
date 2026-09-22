"""Fetch a short definition from Wikipedia using the REST Summary API.

The REST API returns a clean JSON payload with:
- `extract`: the first paragraph (1-3 sentences)
- `type`: "standard" | "disambiguation" | ...

We apply aggressive cleaning to remove:
- IPA pronunciations     (e.g., "[ka.ɡo.ɕi.ma]")
- Parenthetical pronunciation guides (e.g., "(/t͡ʃɛɚ/)")
- Foreign-script parens  (e.g., "(Japanese: 鹿児島市, Hepburn: ...)")
"""

from __future__ import annotations

import re
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("definitions.wikipedia")

_HEADERS = {"User-Agent": settings.user_agent}
_MAX_LEN = 250
_BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

# --- Cleaning patterns ------------------------------------------------------

# IPA-like brackets:  [ka.ɡo.ɕi.ma, -maꜜ.ɕi]
_IPA_BRACKETS = re.compile(r"\[[^\]]{2,80}\]")

# Parentheses containing IPA symbols or slashes:  (/t͡ʃɛɚ/), (/ˈaɪpiːeɪ/)
_PHONETIC_PARENS = re.compile(r"\(\s*/[^)]{1,60}/\s*\)")

# Parentheses with "Xxx: <non-Latin>" — e.g., (Japanese: 鹿児島市, ...)
_FOREIGN_SCRIPT_PARENS = re.compile(
    r"\(\s*[A-Za-z][A-Za-z\s\-]{2,20}\s*:\s*[^)]*[^\x00-\x7F][^)]*\)",
    re.UNICODE,
)

# Trailing/leading whitespace and doubled spaces after cleaning
_WHITESPACE = re.compile(r"\s+")

# Split on sentence boundaries
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _clean_extract(text: str) -> str:
    """Remove pronunciation guides and foreign-script parentheticals."""
    if not text:
        return text

    # Remove brackets and parentheses patterns
    text = _IPA_BRACKETS.sub("", text)
    text = _PHONETIC_PARENS.sub("", text)
    text = _FOREIGN_SCRIPT_PARENS.sub("", text)

    # Collapse leftover whitespace
    text = _WHITESPACE.sub(" ", text).strip()

    # Clean up orphaned punctuation:  "word , other"  ->  "word, other"
    text = re.sub(r"\s+([,;.!?])", r"\1", text)
    text = re.sub(r"\(\s*\)", "", text)  # empty parens
    text = re.sub(r"\[\s*\]", "", text)  # empty brackets

    return text.strip()


def _first_sentences(text: str, max_len: int) -> str:
    """Return the first full sentence(s) that fit within `max_len`."""
    sentences = _SENTENCE_END.split(text.strip())
    if not sentences:
        return text

    result = ""
    for sentence in sentences:
        candidate = (result + " " + sentence).strip() if result else sentence
        if len(candidate) <= max_len:
            result = candidate
        else:
            # If even the first sentence is too long, truncate it
            if not result:
                result = sentence[: max_len - 3].rstrip() + "..."
            break

    if result and not result.endswith((".", "!", "?")):
        result += "."

    return result


def fetch(term: str) -> str | None:
    """Return the first paragraph of the English Wikipedia article, or None.

    Returns None for disambiguation pages and non-existent articles.
    """
    if not term or not term.strip():
        return None

    url = f"{_BASE_URL}/{quote(term.strip(), safe='')}"

    try:
        with httpx.Client(timeout=settings.wikipedia_timeout, headers=_HEADERS) as client:
            response = client.get(url)
            if response.status_code == 404:
                log.debug(f"Wikipedia: no article for '{term}'")
                return None
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        log.warning(f"Wikipedia HTTP error for '{term}': {exc}")
        return None
    except ValueError as exc:
        log.warning(f"Wikipedia invalid JSON for '{term}': {exc}")
        return None

    # Reject disambiguation pages
    if data.get("type") == "disambiguation":
        log.info(f"Wikipedia: disambiguation page for '{term}'; skipping.")
        return None

    extract = (data.get("extract") or "").strip()
    if not extract or len(extract) < 20:
        return None

    # Clean the extract and take the first sentence(s)
    cleaned = _clean_extract(extract)
    if len(cleaned) < 20:
        return None

    return _first_sentences(cleaned, _MAX_LEN)
