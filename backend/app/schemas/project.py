"""Pydantic schemas for Project endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStatus
from app.schemas.source import ProjectSourceRead

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------


class ProjectCreateEmpty(BaseModel):
    """Body of POST /api/projects — create an empty project.

    Sources are added separately via `/api/projects/{id}/sources/*`.
    """

    title: str = Field(..., min_length=1, max_length=255)

    # Pipeline options
    num_terms: int = Field(default=500, ge=1, le=2000)
    terms_per_1k_words: float = Field(default=15.0, ge=1.0, le=100.0)
    translate_terms: bool = True
    translate_definitions: bool = True
    translation_provider: str = Field(default="argos", pattern=r"^[a-z0-9_\-]+$")
    processing_mode: str = Field(default="offline", pattern=r"^(offline|ai|hybrid)$")
    use_spacy: bool = True
    use_rake: bool = True
    use_yake: bool = True
    use_ner: bool = True

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v


class ProcessRequest(BaseModel):
    """Body of POST /api/process/{id} — pipeline options."""

    num_terms: int = Field(default=500, ge=1, le=2000)
    terms_per_1k_words: float = Field(default=15.0, ge=1.0, le=100.0)
    translate_terms: bool = True
    translate_definitions: bool = True
    translation_provider: str = Field(default="argos", pattern=r"^[a-z0-9_\-]+$")
    processing_mode: str = Field(default="offline", pattern=r"^(offline|ai|hybrid)$")
    use_spacy: bool = True
    use_rake: bool = True
    use_yake: bool = True
    use_ner: bool = True


class ProjectUpdate(BaseModel):
    """Body of PATCH /api/projects/{id} — update title/options."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    num_terms: int | None = Field(default=None, ge=1, le=2000)
    terms_per_1k_words: float | None = Field(default=None, ge=1.0, le=100.0)
    translate_terms: bool | None = None
    translate_definitions: bool | None = None
    translation_provider: str | None = Field(default=None, pattern=r"^[a-z0-9_\-]+$")
    processing_mode: str | None = Field(default=None, pattern=r"^(offline|ai|hybrid)$")
    use_spacy: bool | None = None
    use_rake: bool | None = None
    use_yake: bool | None = None
    use_ner: bool | None = None


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


class ProjectSummary(BaseModel):
    """Short representation for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: ProjectStatus
    word_count: int
    source_count: int
    num_terms: int
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None


class ProjectRead(ProjectSummary):
    """Full representation, includes sources and options."""

    translate_terms: bool
    translate_definitions: bool
    terms_per_1k_words: float
    translation_provider: str
    processing_mode: str
    use_spacy: bool
    use_rake: bool
    use_yake: bool
    use_ner: bool
    error_message: str | None = None
    started_at: datetime | None = None
    sources: list[ProjectSourceRead] = Field(default_factory=list)
    book_metadata: dict | None = None


class ProjectListResponse(BaseModel):
    """Response for GET /api/projects."""

    items: list[ProjectSummary]
    total: int
    page: int = 1
    page_size: int = 50


# ---------------------------------------------------------------------------
# Book metadata
# ---------------------------------------------------------------------------


class BookMetadataUpdate(BaseModel):
    """Body of PUT /api/projects/{id}/metadata.

    Accepts the full BookSpecsTemplate.json structure. Any subset of
    fields is allowed; we store the JSON blob as-is.
    """

    model_config = ConfigDict(extra="allow")

    book_metadata: dict | None = None
    content_classification: dict | None = None
    audience_analysis: dict | None = None
    stylistic_analysis: dict | None = None
    translation_guidelines: dict | None = None
