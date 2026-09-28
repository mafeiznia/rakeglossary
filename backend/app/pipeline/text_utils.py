"""Text normalization helpers for Persian output.

LLMs sometimes produce Arabic lookalike characters (ي U+064A, ك U+0643,
ى U+0649) instead of their Persian counterparts (ی U+06CC, ک U+06A9).
Visually they are similar, but they break search, sort, and copy-paste.
This module normalizes them to the Persian standard.
"""

from __future__ import annotations

# Character mapping: Arabic lookalikes -> Persian equivalents.
# Only affects characters that are visually near-identical but
# semantically different in Persian text.
_PERSIAN_NORMALIZE_MAP = {
    "\u064a": "\u06cc",  # Arabic yeh        -> Persian yeh
    "\u0649": "\u06cc",  # Arabic alef maksura -> Persian yeh
    "\u0643": "\u06a9",  # Arabic kaf        -> Persian keheh
    "\u06aa": "\u06a9",  # Arabic swash kaf  -> Persian keheh
}


def normalize_persian(text: str) -> str:
    """Normalize Arabic lookalike characters to their Persian equivalents.

    Idempotent: running it twice yields the same result as once.

    Args:
        text: Input string, possibly containing Arabic lookalikes.

    Returns:
        String with Arabic lookalikes replaced by Persian characters.
    """
    if not text:
        return text
    for src, dst in _PERSIAN_NORMALIZE_MAP.items():
        text = text.replace(src, dst)
    return text
