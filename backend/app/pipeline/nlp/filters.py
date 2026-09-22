"""Smart filters for candidate keywords (no destructive stripping)."""

from __future__ import annotations

import re
import unicodedata

from app.pipeline.nlp.candidates import Candidate
from app.pipeline.nlp.stopwords import english_stopwords

_MIN_LEN = 2
_MAX_LEN = 80
_MAX_WORDS = 4
_ALNUM_RE = re.compile(r"[A-Za-z\u0600-\u06FF]")
_DIGIT_ONLY_RE = re.compile(r"^\d+$")
_ALLOWED_RE = re.compile(r"^[\w\s\-/+.()&']+$", re.UNICODE)

_BAD_BOUNDARY_WORDS: frozenset[str] = frozenset(
    {
        "from",
        "since",
        "with",
        "without",
        "for",
        "by",
        "to",
        "of",
        "in",
        "on",
        "at",
        "as",
        "than",
        "into",
        "onto",
        "upon",
        "over",
        "under",
        "between",
        "before",
        "after",
        "during",
        "through",
        "across",
        "along",
        "among",
        "against",
        "toward",
        "towards",
        "within",
        "beyond",
        "above",
        "below",
        "and",
        "or",
        "but",
        "if",
        "when",
        "while",
        "because",
        "although",
        "though",
        "unless",
        "until",
        "till",
        "so",
        "yet",
        "he",
        "she",
        "it",
        "they",
        "we",
        "you",
        "i",
        "him",
        "her",
        "them",
        "us",
        "his",
        "hers",
        "its",
        "their",
        "our",
        "your",
        "my",
        "me",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "am",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "will",
        "would",
        "shall",
        "should",
        "can",
        "could",
        "may",
        "might",
        "must",
        "ought",
    }
)


def normalize(term: str) -> str:
    """Normalize whitespace, unicode, and strip edge punctuation."""
    term = unicodedata.normalize("NFKC", term)
    term = re.sub(r"\s+", " ", term).strip()
    term = term.strip(" \t.,;:!?\"'`()[]{}")
    return term


def _has_bad_boundary(term: str) -> bool:
    words = term.lower().split()
    if not words:
        return True
    return words[0] in _BAD_BOUNDARY_WORDS or words[-1] in _BAD_BOUNDARY_WORDS


def is_valid(
    candidate: Candidate,
    extra_stopwords: frozenset[str] = frozenset(),
) -> bool:
    """Return True if the candidate survives all quality checks."""
    term = normalize(candidate.term)
    if not term:
        return False
    if len(term) < _MIN_LEN or len(term) > _MAX_LEN:
        return False
    if len(term.split()) > _MAX_WORDS:
        return False
    if _DIGIT_ONLY_RE.match(term):
        return False
    if not _ALNUM_RE.search(term):
        return False
    if not _ALLOWED_RE.match(term):
        return False
    if _has_bad_boundary(term):
        return False

    stop = english_stopwords() | extra_stopwords
    meaningful = [w for w in term.lower().split() if w not in stop]
    return bool(meaningful)


def deduplicate(candidates: list[Candidate]) -> list[Candidate]:
    """Remove duplicates using a case-insensitive, space-normalized key."""
    seen: dict[str, Candidate] = {}
    for c in candidates:
        key = normalize(c.term).lower()
        if key in seen:
            if c.raw_score > seen[key].raw_score:
                seen[key] = c
        else:
            seen[key] = c
    return list(seen.values())
