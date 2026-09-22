"""ProjectSource ORM model — one file or text snippet that belongs to a project."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
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
    from app.models.project import Project


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SourceType(str, Enum):
    FILE = "file"
    TEXT = "text"


class ProjectSource(Base):
    """A single input source for a project (uploaded file or pasted text)."""

    __tablename__ = "project_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, native_enum=False, length=16), nullable=False
    )

    # For file sources
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # For text sources
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Display name (original filename or user-provided label)
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    included: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    project: Mapped[Project] = relationship("Project", back_populates="sources")

    def __repr__(self) -> str:
        return (
            f"<ProjectSource #{self.id} type={self.source_type.value} "
            f"name={self.original_name!r}>"
        )
