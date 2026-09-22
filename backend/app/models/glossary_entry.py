"""GlossaryEntry ORM model — one row of a generated glossary."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.project import Project


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class GlossaryEntry(Base):
    __tablename__ = "glossary_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Core fields (always present) ---
    english_term: Mapped[str] = mapped_column(String(255), nullable=False)
    persian_term: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    english_definition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    persian_definition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- AI Mode extras (nullable, only filled in AI mode) ---
    pos: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    persian_alternatives: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON-encoded list
    translator_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    persian_transliteration: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    project: Mapped[Project] = relationship("Project", back_populates="entries")

    def __repr__(self) -> str:
        return f"<GlossaryEntry #{self.id} term={self.english_term!r}>"
