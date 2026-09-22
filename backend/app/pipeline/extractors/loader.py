"""Select the correct extractor based on file extension, or accept raw text."""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.pipeline.extractors.base import DocumentExtractor
from app.pipeline.extractors.docx import DocxExtractor
from app.pipeline.extractors.epub import EpubExtractor
from app.pipeline.extractors.pdf import PdfExtractor
from app.pipeline.extractors.txt import TxtExtractor

log = get_logger("extractor.loader")

_EXTRACTORS: tuple[DocumentExtractor, ...] = (
    PdfExtractor(),
    DocxExtractor(),
    EpubExtractor(),
    TxtExtractor(),
)


def _build_registry() -> dict[str, DocumentExtractor]:
    registry: dict[str, DocumentExtractor] = {}
    for extractor in _EXTRACTORS:
        for ext in extractor.supported_extensions:
            registry[ext] = extractor
    return registry


_REGISTRY = _build_registry()


def supported_extensions() -> tuple[str, ...]:
    """Return all extensions the pipeline can handle."""
    return tuple(sorted(_REGISTRY))


def load_text(file_path: str | Path) -> str:
    """Extract text from `file_path` using the appropriate extractor.

    Returns an empty string on unsupported formats or failures.
    """
    path = Path(file_path)
    if not path.exists():
        log.error(f"File does not exist: {path}")
        return ""

    suffix = path.suffix.lower()
    extractor = _REGISTRY.get(suffix)
    if extractor is None:
        log.error(f"Unsupported format '{suffix}'. Supported: {', '.join(supported_extensions())}")
        return ""

    log.info(f"Extracting text from '{path.name}' using {type(extractor).__name__}")
    text = extractor.extract(path)
    log.info(f"Extracted {len(text.split())} words from '{path.name}'")
    return text


def load_text_from_source(
    file_path: str | Path | None = None,
    raw_text: str | None = None,
) -> str:
    """Return text from either a file path or a raw text string.

    Exactly one of `file_path` or `raw_text` must be provided.
    Returns an empty string on failure or invalid input.
    """
    has_file = file_path is not None
    has_text = raw_text is not None

    if has_file and has_text:
        log.error("Provide either file_path or raw_text, not both.")
        return ""
    if has_text:
        text = raw_text or ""
        log.info(f"Using direct text input: {len(text.split())} words.")
        return text.strip()
    if has_file:
        return load_text(file_path)  # type: ignore[arg-type]

    log.error("No input source provided (file_path or raw_text required).")
    return ""
