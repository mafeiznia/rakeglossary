"""Application version and identity metadata."""

from __future__ import annotations

import sys

__version__ = "0.1.0"
APP_NAME = "RakeGlossary"
APP_TAGLINE_FA = "تولیدکننده خودکار واژه‌نامه‌ی دو‌زبانه (انگلیسی → فارسی)"
APP_TAGLINE_EN = "Automated glossary generator (EN → FA)"
LICENSE = "MIT"
COPYRIGHT_YEAR = 2026

AUTHOR_NAME_FA = "محمود اهرپور فیض‌نیا"
AUTHOR_NAME_EN = "Mahmoud Aharpour Feiznia"
AUTHOR_ROLE_FA = "طراحی و توسعه"
AUTHOR_ROLE_EN = "Designed & Developed by"
AUTHOR_EMAIL = "ma.feiznia@gmail.com"
AUTHOR_LINKEDIN = "https://www.linkedin.com/in/mahmoud-aharpour-feiznia-585782265"
AUTHOR_WEBSITE = "https://www.yadoto.ir"
GITHUB_REPO = "https://github.com/mafeiznia/rakeglossary"


def python_version() -> str:
    """Return the running Python version (e.g. '3.12.2')."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
