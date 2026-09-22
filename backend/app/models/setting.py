"""Key-value Setting ORM model (global app settings)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Setting {self.key!r}>"
