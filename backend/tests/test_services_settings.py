"""Tests for settings_service (user stopwords/blacklist)."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.services import settings_service


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:", future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record) -> None:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_get_user_stopwords_empty_by_default(session: Session) -> None:
    assert settings_service.get_user_stopwords(session) == []


def test_set_user_stopwords_normalizes(session: Session) -> None:
    result = settings_service.set_user_stopwords(
        session, ["  Hello ", "WORLD", "hello", ""]
    )
    # lowercased, stripped, deduped (order preserved), empty removed
    assert result == ["hello", "world"]


def test_add_user_stopword_idempotent(session: Session) -> None:
    settings_service.add_user_stopword(session, "Hello")
    settings_service.add_user_stopword(session, "hello")
    settings_service.add_user_stopword(session, "WORLD")

    words = settings_service.get_user_stopwords(session)
    assert words == ["hello", "world"]


def test_remove_user_stopword(session: Session) -> None:
    settings_service.set_user_stopwords(session, ["a", "b", "c"])
    settings_service.remove_user_stopword(session, "B")
    assert settings_service.get_user_stopwords(session) == ["a", "c"]


def test_remove_nonexistent_word_is_noop(session: Session) -> None:
    settings_service.set_user_stopwords(session, ["a"])
    settings_service.remove_user_stopword(session, "zzz")
    assert settings_service.get_user_stopwords(session) == ["a"]


def test_invalid_json_returns_empty(session: Session) -> None:
    settings_service.set_raw(
        session, settings_service.KEY_USER_STOPWORDS, "not json"
    )
    assert settings_service.get_user_stopwords(session) == []