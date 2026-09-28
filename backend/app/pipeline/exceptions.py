"""Shared exceptions for the pipeline package.

Living in its own module so that low-level components (translation,
LLM client) can raise CancelledError without importing the high-level
orchestrator (glossary.py), which would create a circular import.
"""

from __future__ import annotations


class CancelledError(Exception):
    """Raised when the pipeline is cancelled by the user."""
