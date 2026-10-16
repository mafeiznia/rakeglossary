"""CRUD for LLM configuration, persisted in the Settings table.

NOTE: API keys are stored in plaintext in the local SQLite database.
This is acceptable for a single-user desktop app where the DB is
only accessible to the current Windows user. If you later move this
to a shared server, replace with OS keyring / secret storage.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

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


# ---------------------------------------------------------------------------
# User model history (per-provider list, most recent first)
# ---------------------------------------------------------------------------

_USER_MODELS_KEY = "llm_user_models"
_MODELS_CACHE_KEY = "llm_models_cache"
_MODELS_CACHE_TTL_HOURS = 24


def _utcnow() -> datetime:
    """Return the current UTC time. Separated for testability."""
    from datetime import UTC, datetime

    return datetime.now(UTC)


def get_user_models(session: Session) -> dict[str, list[str]]:
    """Return the user's per-provider model history."""
    raw = settings_service.get_raw(session, _USER_MODELS_KEY)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("llm_user_models contains invalid JSON; returning empty.")
        return {}
    if not isinstance(data, dict):
        return {}
    # Normalize: ensure lists of strings
    result: dict[str, list[str]] = {}
    for provider, models in data.items():
        if isinstance(models, list):
            result[str(provider)] = [str(m) for m in models if m]
    return result


def add_user_model(session: Session, provider: str, model: str) -> None:
    """Add a model to the user's history. Moves to front if already present."""
    model = (model or "").strip()
    provider = (provider or "").strip()
    if not provider or not model:
        return

    history = get_user_models(session)
    models = history.get(provider, [])
    # Remove if already present (we'll re-add at front)
    models = [m for m in models if m != model]
    models.insert(0, model)

    # Cap history to 20 entries per provider
    models = models[:20]

    history[provider] = models
    settings_service.set_raw(session, _USER_MODELS_KEY, json.dumps(history, ensure_ascii=False))


def remove_user_model(session: Session, provider: str, model: str) -> None:
    """Remove a model from the user's history."""
    history = get_user_models(session)
    if provider not in history:
        return
    models = [m for m in history[provider] if m != model]
    if models:
        history[provider] = models
    else:
        del history[provider]
    settings_service.set_raw(session, _USER_MODELS_KEY, json.dumps(history, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Fetched models cache (24-hour TTL)
# ---------------------------------------------------------------------------


def get_models_cache(session: Session, provider: str) -> list[str] | None:
    """Return the cached model list for `provider`, or None if missing/expired."""
    raw = settings_service.get_raw(session, _MODELS_CACHE_KEY)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    entry = data.get(provider)
    if not isinstance(entry, dict):
        return None

    fetched_at_raw = entry.get("fetched_at")
    models = entry.get("models")
    if not isinstance(models, list) or not isinstance(fetched_at_raw, str):
        return None

    try:
        fetched_at = datetime.fromisoformat(fetched_at_raw)
    except ValueError:
        return None

    # Handle timezone-aware vs naive (fromisoformat may drop tz)
    now = _utcnow()
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    age = now - fetched_at
    if age > timedelta(hours=_MODELS_CACHE_TTL_HOURS):
        return None

    return [str(m) for m in models if m]


def set_models_cache(session: Session, provider: str, models: list[str]) -> None:
    """Store a fresh list of models for `provider` with a TTL timestamp."""
    raw = settings_service.get_raw(session, _MODELS_CACHE_KEY)
    data: dict = {}
    if raw:
        try:
            existing = json.loads(raw)
            if isinstance(existing, dict):
                data = existing
        except json.JSONDecodeError:
            data = {}

    data[provider] = {
        "models": [str(m) for m in models if m],
        "fetched_at": _utcnow().isoformat(),
    }
    settings_service.set_raw(session, _MODELS_CACHE_KEY, json.dumps(data, ensure_ascii=False))


def clear_models_cache(session: Session, provider: str) -> None:
    """Remove the cached model list for a single provider."""
    raw = settings_service.get_raw(session, _MODELS_CACHE_KEY)
    if not raw:
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    data.pop(provider, None)
    settings_service.set_raw(session, _MODELS_CACHE_KEY, json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Union: list of models available for a provider
# ---------------------------------------------------------------------------


def list_available_models(session: Session, provider: str) -> list[str]:
    """Return the union of user history + cached + suggested models.

    Order of priority (most important first):
      1. User history (most recent first)
      2. Cached models from a provider fetch
      3. Suggested models from llm_providers.json

    Duplicates are removed, keeping the highest-priority occurrence.
    """
    if not provider:
        return []

    from app.pipeline.definitions.llm_providers import get_provider

    ordered: list[str] = []
    seen: set[str] = set()

    def _add(models: list[str]) -> None:
        for m in models:
            m = (m or "").strip()
            if m and m not in seen:
                seen.add(m)
                ordered.append(m)

    # 1. User history
    history = get_user_models(session)
    _add(history.get(provider, []))

    # 2. Cached from fetch
    cached = get_models_cache(session, provider)
    if cached:
        _add(cached)

    # 3. Suggested from JSON
    info = get_provider(provider)
    if info is not None:
        _add(list(info.suggested_models))

    return ordered
