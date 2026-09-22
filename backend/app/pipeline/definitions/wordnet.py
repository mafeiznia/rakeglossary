"""WordNet definition lookup — fully offline, no rate limits.

WordNet is a lexical database of English. It contains short, precise
definitions for common words (nouns, verbs, adjectives). It does not
cover proper names (people, places, brands).
"""

from __future__ import annotations

from functools import lru_cache

import nltk
from nltk.corpus import wordnet as wn

from app.core.logging import get_logger

log = get_logger("definitions.wordnet")

_MAX_LEN = 220


@lru_cache(maxsize=1)
def _ensure_wordnet() -> bool:
    """Download WordNet data on first use. Returns True if available."""
    try:
        # Trigger a lookup to see if the corpus is installed
        wn.synsets("test")
        return True
    except LookupError:
        log.info("WordNet data not found. Downloading (one-time)...")
        try:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            wn.synsets("test")
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Could not download WordNet: {exc}")
            return False


def fetch(term: str) -> str | None:
    """Return the WordNet definition of `term`, or None.

    Uses the most common synset (first result). Only meaningful for
    single-word English terms; multi-word phrases almost never have
    a WordNet entry.
    """
    if not term or not term.strip():
        return None

    # WordNet only handles simple single-word or hyphenated terms
    # (it does have some multi-word entries like "New York", but rare)
    if len(term.split()) > 3:
        return None

    # Reject non-alphabetic terms (e.g., "AI-2024", "3D")
    cleaned = term.strip().replace("-", "").replace("_", "")
    if not cleaned.isalpha():
        return None

    if not _ensure_wordnet():
        return None

    synsets = wn.synsets(term)
    if not synsets:
        return None

    # First synset is the most frequent sense of the word
    definition = synsets[0].definition()
    if not definition or len(definition) < 10:
        return None

    definition = definition.strip()
    if len(definition) > _MAX_LEN:
        definition = definition[:_MAX_LEN].rstrip() + "..."

    return definition
