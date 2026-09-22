"""SQLAlchemy engine, session factory, and Declarative Base."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_DB_PATH: Path = settings.paths.data / "rakeglossary.db"
_DB_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    _DB_URL,
    echo=False,
    future=True,
    # needed because FastAPI runs handlers in a threadpool
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _connection_record) -> None:
    """Enable foreign key enforcement on every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session and close it afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Safe to call on app startup."""
    # Import models so they register with Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
