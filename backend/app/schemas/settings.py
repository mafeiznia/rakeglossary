"""Pydantic schemas for app Settings endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SettingRead(BaseModel):
    """A single key/value setting."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    updated_at: datetime


class SettingUpdate(BaseModel):
    """Body of PUT /api/settings/{key}."""

    value: str = Field(..., description="JSON-encoded value")


# ---------------------------------------------------------------------------
# User stopwords (blacklist) — dedicated schemas
# ---------------------------------------------------------------------------


class UserStopwordsRead(BaseModel):
    """Current list of user-defined stopwords."""

    words: list[str]
    total: int


class UserStopwordAdd(BaseModel):
    """Body of POST /api/settings/stopwords."""

    word: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------


class LlmConfigRead(BaseModel):
    """Current LLM config. API key is masked in responses."""

    enabled: bool
    provider: str
    model: str
    base_url: str | None = None
    has_api_key: bool
    api_key_masked: str | None = None


class LlmConfigUpdate(BaseModel):
    """Body of PUT /api/settings/llm. All fields optional (PATCH-like)."""

    enabled: bool | None = None
    provider: str | None = Field(default=None, pattern=r"^(openai|openrouter|gemini|gapgpt)$")
    api_key: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)


class LlmProviderInfo(BaseModel):
    key: str
    name: str
    default_model: str
    suggested_models: list[str]
    docs_url: str
    base_url: str | None = None


class LlmTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int | None = None
