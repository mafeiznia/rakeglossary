"""CRUD for LLM configuration, persisted in the Settings table.

NOTE: API keys are stored in plaintext in the local SQLite database.
This is acceptable for a single-user desktop app where the DB is
only accessible to the current Windows user. If you later move this
to a shared server, replace with OS keyring / secret storage.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services import settings_service

log = get_logger("services.llm_config")

KEY = "llm_config"


@dataclass
class LlmConfig:
    """Persisted LLM configuration."""

    enabled: bool = False
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str | None = None  # custom override (optional)


def get_config(session: Session) -> LlmConfig:
    """Load the LLM config from settings, applying sensible defaults."""
    raw = settings_service.get_raw(session, KEY)
    if not raw:
        return LlmConfig()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("llm_config contains invalid JSON; returning defaults.")
        return LlmConfig()

    return LlmConfig(
        enabled=bool(data.get("enabled", False)),
        provider=str(data.get("provider", "openai")),
        api_key=str(data.get("api_key", "")),
        model=str(data.get("model", "gpt-4o-mini")),
        base_url=data.get("base_url") or None,
    )


def set_config(session: Session, config: LlmConfig) -> LlmConfig:
    """Persist the LLM config."""
    settings_service.set_raw(
        session,
        KEY,
        json.dumps(asdict(config), ensure_ascii=False),
    )
    log.info(
        f"Updated LLM config: provider={config.provider}, "
        f"model={config.model}, enabled={config.enabled}"
    )
    return config


def clear_config(session: Session) -> None:
    """Remove the LLM config (used by 'Disconnect' button)."""
    row = session.get(__import__("app.models.setting", fromlist=["Setting"]).Setting, KEY)
    if row is not None:
        session.delete(row)
        session.commit()
        log.info("Cleared LLM config.")
