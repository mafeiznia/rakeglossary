"""Plain text extractor with encoding auto-detection."""

from __future__ import annotations

from pathlib import Path

from charset_normalizer import from_path

from app.core.logging import get_logger
from app.pipeline.extractors.base import DocumentExtractor

log = get_logger("extractor.txt")


class TxtExtractor(DocumentExtractor):
    """Read a text file, auto-detecting its encoding."""

    supported_extensions = (".txt",)

    def extract(self, file_path: Path) -> str:
        if not file_path.exists():
            log.error(f"File not found: {file_path}")
            return ""
        try:
            best = from_path(file_path).best()
            if best is None:
                log.warning(
                    f"Could not detect encoding for '{file_path.name}', falling back to utf-8"
                )
                return file_path.read_text(encoding="utf-8", errors="ignore")
            return str(best)
        except Exception:
            log.exception(f"Failed to read TXT '{file_path.name}'")
            return ""
