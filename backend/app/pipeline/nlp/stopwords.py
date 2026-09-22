"""Stopwords for keyword extraction: NLTK English + domain-specific extras."""

from __future__ import annotations

from functools import lru_cache

import nltk
from nltk.corpus import stopwords as nltk_stopwords

_CUSTOM = frozenset(
    {
        # کتاب‌شناسی و ساختار سند
        "chapter",
        "page",
        "figure",
        "fig",
        "table",
        "volume",
        "appendix",
        "index",
        "preface",
        "introduction",
        "conclusion",
        "summary",
        "contents",
        "section",
        "subsection",
        "part",
        "book",
        "edition",
        # نشر و حقوق
        "isbn",
        "publisher",
        "author",
        "editor",
        "press",
        "rights",
        "reserved",
        "copyright",
        "license",
        "printed",
        "publication",
        # آکادمیک عمومی
        "proceedings",
        "journal",
        "abstract",
        "references",
        "bibliography",
        "university",
        "institute",
        "department",
        "faculty",
        # پرکاربردهای کم‌ارزش
        "example",
        "illustrated",
        "shown",
        "given",
        "however",
        "therefore",
        "thus",
        "hence",
        "moreover",
        "furthermore",
        "whereas",
    }
)

# (resource name, expected path inside NLTK data)
_REQUIRED_RESOURCES: tuple[tuple[str, str], ...] = (
    ("stopwords", "corpora/stopwords"),
    ("punkt", "tokenizers/punkt"),
    ("punkt_tab", "tokenizers/punkt_tab"),
)


@lru_cache(maxsize=1)
def ensure_nltk_data() -> None:
    """Ensure all required NLTK resources are available, downloading if needed."""
    for resource, path in _REQUIRED_RESOURCES:
        try:
            nltk.data.find(path)
        except LookupError:
            # NLTK_ALLOW_PROXIED_URLOPEN is set in app.core.config
            nltk.download(resource, quiet=True)


@lru_cache(maxsize=1)
def english_stopwords() -> frozenset[str]:
    """Return the union of NLTK English stopwords and our custom set."""
    ensure_nltk_data()
    base = set(nltk_stopwords.words("english"))
    return frozenset(base | _CUSTOM)
