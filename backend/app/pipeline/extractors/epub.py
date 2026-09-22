"""EPUB extractor using ebooklib + BeautifulSoup with noise removal."""

from __future__ import annotations

from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from app.core.logging import get_logger
from app.pipeline.extractors.base import DocumentExtractor

log = get_logger("extractor.epub")

_NOISE_TAGS = ("script", "style", "nav", "header", "footer")


class EpubExtractor(DocumentExtractor):
    """Extract visible text from EPUB documents."""

    supported_extensions = (".epub",)

    def extract(self, file_path: Path) -> str:
        if not file_path.exists():
            log.error(f"File not found: {file_path}")
            return ""
        try:
            book = epub.read_epub(str(file_path))
        except Exception:
            log.exception(f"Failed to open EPUB '{file_path.name}'")
            return ""

        parts: list[str] = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                for tag in soup(_NOISE_TAGS):
                    tag.decompose()
                text = soup.get_text(separator="\n")
                if text.strip():
                    parts.append(text)
            except Exception as exc:  # noqa: BLE001
                log.warning(f"Skipped one EPUB item in '{file_path.name}': {exc}")
        return "\n".join(parts)
