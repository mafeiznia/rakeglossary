"""Application-wide configuration.

Loads settings from environment variables with sensible defaults.
Designed for local desktop deployment; no secrets are hard-coded.
"""

from __future__ import annotations

import os

# Allow NLTK to fetch resources through a configured HTTP proxy.
# Required on Windows machines behind a corporate/ISP proxy
# (NLTK >= 3.10 enables SSRF protection that blocks proxied fetches by default).
# Must run before any `import nltk` in the process.
os.environ.setdefault("NLTK_ALLOW_PROXIED_URLOPEN", "1")

from dataclasses import dataclass, field
from pathlib import Path


def _project_root() -> Path:
    """Return the project root directory (RakeGlossary/)."""
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem paths used across the app."""

    root: Path = field(default_factory=_project_root)
    data: Path = field(init=False)
    projects: Path = field(init=False)
    exports: Path = field(init=False)
    cache: Path = field(init=False)
    logs: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", self.root / "data")
        object.__setattr__(self, "projects", self.data / "projects")
        object.__setattr__(self, "exports", self.data / "exports")
        object.__setattr__(self, "cache", self.data / "cache")
        object.__setattr__(self, "logs", self.data / "logs")
        for p in (self.data, self.projects, self.exports, self.cache, self.logs):
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

    # --- HTTP clients ---
    http_timeout: float = float(os.getenv("RG_HTTP_TIMEOUT", "8.0"))
    user_agent: str = os.getenv(
        "RG_USER_AGENT",
        "RakeGlossary/0.1.0 (https://example.invalid; contact@example.invalid)",
    )

    # --- Wikipedia ---
    wikipedia_api: str = os.getenv("RG_WIKI_API", "https://en.wikipedia.org/w/api.php")
    wikipedia_timeout: float = float(os.getenv("RG_WIKI_TIMEOUT", "3.0"))

    # --- Translation rate limiting ---
    translation_rate_limit: float = float(os.getenv("RG_TRANSLATION_RATE_LIMIT", "4.0"))
    translation_max_retries: int = int(os.getenv("RG_TRANSLATION_MAX_RETRIES", "4"))
    translation_retry_base_delay: float = float(os.getenv("RG_TRANSLATION_RETRY_DELAY", "1.5"))
    translation_batch_size: int = int(os.getenv("RG_TRANSLATION_BATCH_SIZE", "25"))

    # --- LLM ---
    llm_timeout: float = float(os.getenv("RG_LLM_TIMEOUT", "30.0"))
    llm_max_tokens: int = int(os.getenv("RG_LLM_MAX_TOKENS", "80"))
    llm_temperature: float = float(os.getenv("RG_LLM_TEMPERATURE", "0.3"))

    # --- Paths ---
    paths: Paths = field(default_factory=Paths)


settings = Settings()
