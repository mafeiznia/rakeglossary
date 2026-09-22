"""Text preprocessing before keyword extraction."""

from __future__ import annotations

import re

from app.core.logging import get_logger

log = get_logger("nlp.preprocess")

# بازه‌های کاراکترهای غیرمجاز (نویز PDF/HTML)
_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
# حذف ارجاع‌های داخل متن مثل [1] یا (Smith, 2020)
_REFERENCE_RE = re.compile(r"\[\d{1,3}\]|\(\s*[A-Z][a-zA-Z]+(?:\s+et\s+al\.)?,?\s+\d{4}\s*\)")
# حذف شماره صفحات انتهای خطوط
_PAGE_NUM_RE = re.compile(r"\n\s*\d{1,4}\s*\n")


def clean_text(text: str) -> str:
    """Normalize whitespace and remove common PDF/HTML noise."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _REFERENCE_RE.sub(" ", text)
    text = _PAGE_NUM_RE.sub("\n", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()
