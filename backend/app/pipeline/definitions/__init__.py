"""Definition resolution package."""

from app.pipeline.definitions.resolver import (
    DefinitionResult,
    DefinitionSource,
    resolve,
    resolve_classic,
)

__all__ = [
    "DefinitionResult",
    "DefinitionSource",
    "resolve",
    "resolve_classic",
]
