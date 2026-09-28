"""Regression tests for pipeline cancellation.

Ensures that translate_many functions (both LLM-based and classic
providers) respect a cancel_event and raise CancelledError promptly
instead of running to completion after the user has pressed Stop.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.pipeline import llm_client
from app.pipeline.glossary import CancelledError
from app.services import llm_config_service


@pytest.fixture
def session(monkeypatch) -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record) -> None:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        import app.pipeline.llm_client as llm_module_imported

        monkeypatch.setattr(llm_module_imported, "SessionLocal", lambda: _SameSession(s))
        yield s


class _SameSession:
    def __init__(self, session: Session) -> None:
        self._session = session

    def __enter__(self) -> Session:
        return self._session

    def __exit__(self, *args) -> None:
        return None


def _configure_llm(session: Session) -> None:
    llm_config_service.set_config(
        session,
        llm_config_service.LlmConfig(
            enabled=True,
            provider="openai",
            api_key="sk-test",
            model="gpt-4o-mini",
        ),
    )


# ---------------------------------------------------------------------------
# Bug 5: translate_many does not respect cancel_event
# ---------------------------------------------------------------------------


def test_llm_translate_many_accepts_cancel_event(session: Session) -> None:
    """Regression: llm_client.translate_many must accept a cancel_event."""
    _configure_llm(session)
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(CancelledError):
        llm_client.translate_many(["hello", "world"], cancel_event=cancel_event)


def test_llm_translate_many_cancels_before_api_call(session: Session) -> None:
    """Regression: if cancel_event is set, no API call should be made."""
    _configure_llm(session)
    cancel_event = threading.Event()
    cancel_event.set()

    mock_client = MagicMock()
    with patch("openai.OpenAI", return_value=mock_client):
        with pytest.raises(CancelledError):
            llm_client.translate_many(["hello"], cancel_event=cancel_event)

    mock_client.chat.completions.create.assert_not_called()


def test_service_translate_many_accepts_cancel_event() -> None:
    """Regression: translation.service.translate_many must accept cancel_event."""
    from app.pipeline.translation.service import translate_many

    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(CancelledError):
        translate_many(["hello", "world"], cancel_event=cancel_event)
