"""Application-wide configuration.

Loads settings from environment variables with sensible defaults.
Designed for local desktop deployment; no secrets are hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _project_root() -> Path:
    """Return the project root directory (RakeGlossary/).

    This file lives at <root>/backend/app/core/config.py, so we go up
    four levels: core -> app -> backend -> root.
    """
    return Path(__file__).resolve().parents[3]


def _data_root() -> Path:
    """Return the runtime data directory.

    Honors the ``RG_DATA_DIR`` environment variable, which the desktop
    launcher sets in production (pointing to ``%APPDATA%/RakeGlossary/data``).
    Falls back to ``<project_root>/data`` for development.
    """
    override = os.getenv("RG_DATA_DIR")
    if override:
        return Path(override)
    return _project_root() / "data"


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem paths used across the app."""

    root: Path = field(default_factory=_project_root)
    data: Path = field(default_factory=_data_root)
    uploads: Path = field(init=False)
    exports: Path = field(init=False)
    cache: Path = field(init=False)
    logs: Path = field(init=False)
    projects: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "uploads", self.data / "uploads")
        object.__setattr__(self, "exports", self.data / "exports")
        object.__setattr__(self, "cache", self.data / "cache")
        object.__setattr__(self, "logs", self.data / "logs")
        object.__setattr__(self, "projects", self.data / "projects")
        for p in (
            self.data,
            self.uploads,
            self.exports,
            self.cache,
            self.logs,
            self.projects,
        ):
            p.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    """Runtime settings, overridable via environment variables."""

    # --- Server ---
    host: str = os.getenv("RG_HOST", "127.0.0.1")
    port: int = int(os.getenv("RG_PORT", "8765"))
    log_level: str = os.getenv("RG_LOG_LEVEL", "INFO")

    # --- Pipeline defaults ---
    default_num_terms: int = int(os.getenv("RG_NUM_TERMS", "500"))

    # --- Translation ---
    translation_provider: str = os.getenv("RG_TRANSLATION_PROVIDER", "google")
    libre_translate_url: str = os.getenv("RG_LIBRE_URL", "http://127.0.0.1:5000")
    translation_rate_limit: float = float(os.getenv("RG_TRANSLATION_RATE_LIMIT", "4.0"))
    translation_max_retries: int = int(os.getenv("RG_TRANSLATION_MAX_RETRIES", "4"))
    translation_retry_base_delay: float = float(os.getenv("RG_TRANSLATION_RETRY_BASE_DELAY", "0.5"))
    translation_batch_size: int = int(os.getenv("RG_TRANSLATION_BATCH_SIZE", "25"))

    # --- Wikipedia ---
    wikipedia_api: str = os.getenv("RG_WIKI_API", "https://en.wikipedia.org/w/api.php")
    wikipedia_timeout: float = float(os.getenv("RG_WIKI_TIMEOUT", "3.0"))

    # --- HTTP ---
    http_timeout: float = float(os.getenv("RG_HTTP_TIMEOUT", "8.0"))
    user_agent: str = os.getenv(
        "RG_USER_AGENT",
        "RakeGlossary/0.1.0 (+https://github.com/mafeiznia/rakeglossary)",
    )

    # --- LLM ---
    llm_timeout: float = float(os.getenv("RG_LLM_TIMEOUT", "30.0"))
    llm_max_tokens: int = int(os.getenv("RG_LLM_MAX_TOKENS", "80"))
    llm_temperature: float = float(os.getenv("RG_LLM_TEMPERATURE", "0.3"))

    # --- Paths ---
    paths: Paths = field(default_factory=Paths)


settings = Settings()
