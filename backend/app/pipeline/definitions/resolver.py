"""Resolve a definition for a term using the classic layered fallback.

Used only in `offline` and `hybrid` processing modes. In `ai` mode,
definitions come directly from the LLM (see `llm_client.fetch_definition`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

log = get_logger("definitions.resolver")


class DefinitionSource(str, Enum):
    IN_TEXT = "In-Text"
    WIKIPEDIA = "Wikipedia"
    WORDNET = "WordNet"
    LLM = "LLM"
    NONE = "None"


@dataclass(frozen=True)
class DefinitionResult:
    text: str
    source: DefinitionSource


_NOT_FOUND = "No definition found."
_MAX_WIKI_WORDS = 3

_NON_TERM_WORDS = frozenset(
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
        "and",
        "or",
        "but",
        "if",
        "when",
        "while",
        "because",
        "although",
        "though",
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
        "his",
        "hers",
        "its",
        "their",
        "our",
        "your",
        "my",
        "me",
        "happened",
        "became",
        "was",
        "were",
        "is",
        "are",
        "be",
        "been",
        "being",
    }
)


def _is_wiki_worthy(term: str) -> bool:
    words = term.lower().split()
    if not words or len(words) > _MAX_WIKI_WORDS:
        return False
    return not any(w in _NON_TERM_WORDS for w in words)


def resolve_classic(term: str, text: str) -> DefinitionResult:
    """In-text → Wikipedia → WordNet → None."""
    # Lazy imports to avoid circular dependencies
    from app.pipeline.definitions import in_text, wikipedia, wordnet

    definition = in_text.find_in_text(term, text)
    if definition:
        return DefinitionResult(text=definition, source=DefinitionSource.IN_TEXT)

    if _is_wiki_worthy(term):
        definition = wikipedia.fetch(term)
        if definition:
            return DefinitionResult(text=definition, source=DefinitionSource.WIKIPEDIA)

    definition = wordnet.fetch(term)
    if definition:
        return DefinitionResult(text=definition, source=DefinitionSource.WORDNET)

    return DefinitionResult(text=_NOT_FOUND, source=DefinitionSource.NONE)


# Backwards-compatible alias
def resolve(term: str, text: str) -> DefinitionResult:
    return resolve_classic(term, text)
