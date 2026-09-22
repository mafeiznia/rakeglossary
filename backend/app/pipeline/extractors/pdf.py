"""PDF extractor using PyMuPDF (imported as `pymupdf`)."""

from __future__ import annotations

from pathlib import Path

import pymupdf  # modern import; replaces deprecated `import fitz`

from app.core.logging import get_logger
from app.pipeline.extractors.base import DocumentExtractor

log = get_logger("extractor.pdf")


class PdfExtractor(DocumentExtractor):
    """Extract text from text-based PDFs (no OCR)."""

    supported_extensions = (".pdf",)

    def extract(self, file_path: Path) -> str:
        if not file_path.exists():
            log.error(f"File not found: {file_path}")
            return ""
        parts: list[str] = []
        try:
            with pymupdf.open(file_path) as doc:
                for page_index, page in enumerate(doc, start=1):
                    text = page.get_text("text") or ""
                    if text.strip():
                        parts.append(text)
                    else:
                        log.debug(f"Empty page {page_index}/{doc.page_count} in {file_path.name}")
        except Exception:
            log.exception(f"Failed to read PDF '{file_path.name}'")
            return ""
        return "\n".join(parts)
