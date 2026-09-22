"""Project ORM model — metadata and processing options for a glossary."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from itertools import count
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.glossary_entry import GlossaryEntry
    from app.models.project_source import ProjectSource


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


_ORDER_SEQ = count()


class ProjectStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingMode(str, Enum):
    OFFLINE = "offline"
    AI = "ai"
    HYBRID = "hybrid"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_seq: Mapped[int] = mapped_column(
        Integer, default=lambda: next(_ORDER_SEQ), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status / progress
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, native_enum=False, length=16),
        default=ProjectStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Processing options
    num_terms: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    terms_per_1k_words: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    translate_terms: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    translate_definitions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    translation_provider: Mapped[str] = mapped_column(String(32), default="google", nullable=False)
    book_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_mode: Mapped[ProcessingMode] = mapped_column(
        SAEnum(ProcessingMode, native_enum=False, length=16),
        default=ProcessingMode.OFFLINE,
        nullable=False,
    )
    use_spacy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_rake: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_yake: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_ner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Cached aggregates (recomputed whenever sources change)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    sources: Mapped[list[ProjectSource]] = relationship(
        "ProjectSource",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectSource.order_index.asc(), ProjectSource.id.asc()",
    )
    entries: Mapped[list[GlossaryEntry]] = relationship(
        "GlossaryEntry",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="GlossaryEntry.score.desc()",
    )

    def __repr__(self) -> str:
        return f"<Project {self.id[:8]} title={self.title!r} status={self.status.value}>"
