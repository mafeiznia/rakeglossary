"""Pydantic schemas for ProjectSource endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_source import SourceType


class ProjectSourceRead(BaseModel):
    """A single project source, as returned by the API.

    Note: `text_content` is intentionally NOT exposed (could be megabytes)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: str
    source_type: SourceType
    original_name: str
    path: str | None = None
    word_count: int
    order_index: int
    included: bool
    created_at: datetime
    updated_at: datetime


class TextSourceCreate(BaseModel):
    """Body of POST /api/projects/{id}/sources/text."""

    name: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectSourceUpdate(BaseModel):
    """Body of PATCH /api/projects/{id}/sources/{sid}."""

    original_name: str | None = Field(default=None, min_length=1, max_length=255)
    included: bool | None = None
