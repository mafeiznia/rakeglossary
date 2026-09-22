"""App settings endpoints (key/value) + user-stopwords + LLM config."""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.core.logging import get_logger
from app.models.setting import Setting
from app.pipeline import llm_client
from app.pipeline.definitions.llm_providers import list_providers
from app.schemas.settings import (
    LlmConfigRead,
    LlmConfigUpdate,
    LlmProviderInfo,
    LlmTestResult,
    SettingRead,
    SettingUpdate,
    UserStopwordAdd,
    UserStopwordsRead,
)
from app.services import llm_config_service, settings_service

log = get_logger("api.settings")

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# User stopwords (blacklist)
#
# IMPORTANT: these routes MUST be declared BEFORE the generic `/{key}` routes
# below. FastAPI matches routes in declaration order, so if `/{key}` came
# first, requests to `/stopwords` would be captured as a setting key.
# ---------------------------------------------------------------------------


@router.get(
    "/stopwords",
    response_model=UserStopwordsRead,
    summary="List user-defined stopwords (blacklist)",
)
def list_stopwords(session: SessionDep) -> UserStopwordsRead:
    words = settings_service.get_user_stopwords(session)
    return UserStopwordsRead(words=words, total=len(words))


@router.post(
    "/stopwords",
    response_model=UserStopwordsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a word to the blacklist",
)
def add_stopword(
    payload: UserStopwordAdd,
    session: SessionDep,
) -> UserStopwordsRead:
    words = settings_service.add_user_stopword(session, payload.word)
    return UserStopwordsRead(words=words, total=len(words))


@router.delete(
    "/stopwords/{word}",
    response_model=UserStopwordsRead,
    summary="Remove a word from the blacklist",
)
def remove_stopword(word: str, session: SessionDep) -> UserStopwordsRead:
    words = settings_service.remove_user_stopword(session, word)
    return UserStopwordsRead(words=words, total=len(words))


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------


def _mask_key(key: str) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def _to_read(cfg: llm_config_service.LlmConfig) -> LlmConfigRead:
    return LlmConfigRead(
        enabled=cfg.enabled,
        provider=cfg.provider,
        model=cfg.model,
        base_url=cfg.base_url,
        has_api_key=bool(cfg.api_key),
        api_key_masked=_mask_key(cfg.api_key),
    )


@router.get(
    "/llm/providers",
    response_model=list[LlmProviderInfo],
    summary="List available LLM providers",
)
def list_llm_providers() -> list[LlmProviderInfo]:
    return [
        LlmProviderInfo(
            key=p.key,
            name=p.name,
            default_model=p.default_model,
            suggested_models=list(p.suggested_models),
            docs_url=p.docs_url,
            base_url=p.base_url,
        )
        for p in list_providers()
    ]


@router.get(
    "/llm",
    response_model=LlmConfigRead,
    summary="Get the current LLM configuration",
)
def get_llm_config(session: SessionDep) -> LlmConfigRead:
    cfg = llm_config_service.get_config(session)
    return _to_read(cfg)


@router.put(
    "/llm",
    response_model=LlmConfigRead,
    summary="Update the LLM configuration (partial)",
)
def update_llm_config(
    payload: LlmConfigUpdate,
    session: SessionDep,
) -> LlmConfigRead:
    current = llm_config_service.get_config(session)
    data = payload.model_dump(exclude_unset=True)

    provider_changed = (
        "provider" in data and data["provider"] is not None and data["provider"] != current.provider
    )

    if "enabled" in data and data["enabled"] is not None:
        current.enabled = data["enabled"]
    if "provider" in data and data["provider"] is not None:
        current.provider = data["provider"]
    if "api_key" in data and data["api_key"] is not None:
        current.api_key = data["api_key"]
    if "model" in data and data["model"] is not None:
        current.model = data["model"]
    if "base_url" in data:
        current.base_url = data["base_url"] or None

    # If the provider changed and the caller didn't provide a new key,
    # clear the old key (it belongs to the previous provider).
    if provider_changed and not data.get("api_key"):
        log.info(f"Provider changed ({current.provider}); clearing stored API key.")
        current.api_key = ""

    updated = llm_config_service.set_config(session, current)
    return _to_read(updated)


@router.delete(
    "/llm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear LLM configuration",
)
def clear_llm_config(session: SessionDep) -> None:
    llm_config_service.clear_config(session)


@router.post(
    "/llm/test",
    response_model=LlmTestResult,
    summary="Test the current LLM configuration with a sample call",
)
def test_llm_config(session: SessionDep) -> LlmTestResult:
    cfg = llm_config_service.get_config(session)
    if not cfg.enabled:
        return LlmTestResult(success=False, message="LLM is disabled.")
    if not cfg.api_key:
        return LlmTestResult(success=False, message="No API key configured.")

    start = time.monotonic()
    try:
        result = llm_client.fetch_definition("photosynthesis", context="")
    except Exception as exc:  # noqa: BLE001
        return LlmTestResult(success=False, message=f"Error: {exc}")
    latency = int((time.monotonic() - start) * 1000)

    if not result:
        return LlmTestResult(
            success=False,
            message="LLM returned no response. Check model name and API key.",
            latency_ms=latency,
        )

    return LlmTestResult(
        success=True,
        message=f"Received: {result[:80]}",
        latency_ms=latency,
    )


# ---------------------------------------------------------------------------
# Raw key/value settings (generic)
#
# Declared LAST so that `/stopwords` and `/llm/*` are matched first.
# ---------------------------------------------------------------------------


@router.get("", response_model=list[SettingRead], summary="List all settings")
def list_settings(session: SessionDep) -> list[SettingRead]:
    rows = session.execute(select(Setting).order_by(Setting.key)).scalars().all()
    return [SettingRead.model_validate(r) for r in rows]


@router.get(
    "/{key}",
    response_model=SettingRead,
    summary="Get a single setting by key",
)
def get_setting(key: str, session: SessionDep) -> SettingRead:
    row = session.get(Setting, key)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found.",
        )
    return SettingRead.model_validate(row)


@router.put(
    "/{key}",
    response_model=SettingRead,
    summary="Create or update a setting",
)
def upsert_setting(
    key: str,
    payload: SettingUpdate,
    session: SessionDep,
) -> SettingRead:
    try:
        json.loads(payload.value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"value must be valid JSON: {exc}",
        ) from exc

    row = settings_service.set_raw(session, key, payload.value)
    return SettingRead.model_validate(row)


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a setting",
)
def delete_setting(key: str, session: SessionDep) -> None:
    row = session.get(Setting, key)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found.",
        )
    session.delete(row)
    session.commit()
