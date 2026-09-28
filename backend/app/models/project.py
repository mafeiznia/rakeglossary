"""Project ORM model — metadata and processing options for a glossary."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    event,
    func,
    select,
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


# Note: order_seq is assigned in a `before_insert` listener below.
# We deliberately avoid a module-level itertools.count() because it
# would reset to 0 on every server restart and produce duplicate
# order_seq values across sessions.


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
    order_seq: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
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


# ---------------------------------------------------------------------------
# Assign order_seq from the current DB state (not from an in-memory counter)
# ---------------------------------------------------------------------------


@event.listens_for(Project, "before_insert")
def _assign_order_seq(mapper, connection, target) -> None:
    """Assign the next order_seq by querying the max from the database.

    Runs before INSERT, so the value is always derived from persisted
    state. This survives server restarts and never produces duplicates.
    """
    if target.order_seq:
        return
    max_seq = connection.execute(select(func.max(Project.__table__.c.order_seq))).scalar()
    target.order_seq = (max_seq or 0) + 1
