"""Document extractors package."""

from app.pipeline.extractors.loader import (
    load_text,
    load_text_from_source,
    supported_extensions,
)

__all__ = ["load_text", "load_text_from_source", "supported_extensions"]
