"""Pydantic schemas for GlossaryEntry endpoints."""

from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GlossaryEntryRead(BaseModel):
    """A single glossary row returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: str
    english_term: str
    persian_term: str
    english_definition: str
    persian_definition: str
    source: str
    score: float
    frequency: int
    context: str
    is_edited: bool
    # --- AI Mode extras ---
    pos: str | None = None
    category: str | None = None
    persian_alternatives: list[str] | None = None
    translator_note: str | None = None
    persian_transliteration: str | None = None
    # --- Timestamps ---
    created_at: datetime
    updated_at: datetime

    @field_validator("persian_alternatives", mode="before")
    @classmethod
    def _parse_persian_alternatives(cls, v):
        """Accept either a JSON string (from ORM) or a list."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if x]
                return None
            except json.JSONDecodeError:
                return None
        return None


class GlossaryEntryUpdate(BaseModel):
    """Body of PATCH /api/glossary/{id} — manual edits."""

    persian_term: str | None = Field(default=None, max_length=255)
    persian_definition: str | None = None
    english_definition: str | None = None
    translator_note: str | None = None
    is_edited: bool | None = None


class GlossaryResponse(BaseModel):
    """Response for GET /api/projects/{id}/glossary."""

    project_id: str
    entries: list[GlossaryEntryRead]
    total: int
