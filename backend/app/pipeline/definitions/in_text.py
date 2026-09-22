"""Find definitions of a term directly inside the source text."""

from __future__ import annotations

import re

from app.core.logging import get_logger

log = get_logger("definitions.in_text")

# Pattern templates around a term. `{t}` is the escaped term.
_PATTERNS = (
    r"\b{t}\b\s+(?:is\s+defined\s+as|refers?\s+to|means?|is\s+(?:a|an))\s+([^.\n]+)",
    r"\b{t}\b[^.\n]{{0,80}}?(?:defined|described|known)\s+as\s+([^.\n]+)",
    r"\b{t}\b\s*[:\-–—]\s*([^.\n]+)",
)

_MIN_DEF_LEN = 12
_MAX_DEF_LEN = 220


def find_in_text(term: str, text: str) -> str | None:
    """Return a short definition found in `text`, or None."""
    if not term or not text:
        return None
    escaped = re.escape(term)
    for template in _PATTERNS:
        pattern = template.format(t=escaped)
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        definition = match.group(1).strip()
        if len(definition) < _MIN_DEF_LEN:
            continue
        if len(definition) > _MAX_DEF_LEN:
            definition = definition[:_MAX_DEF_LEN].rstrip() + "..."
        return definition
    return None
