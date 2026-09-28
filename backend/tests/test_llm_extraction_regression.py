"""Regression tests for LLM extraction bugs.

Each test reproduces a specific bug found in the past. If a bug is
reintroduced, the corresponding test will fail.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.pipeline import llm_client
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


def _mock_response(content: str) -> MagicMock:
    resp = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Bug 1: len(None) crash when 'glossary' key is missing or null
# ---------------------------------------------------------------------------


def test_extract_handles_missing_glossary_key(session: Session) -> None:
    """Regression: response without 'glossary' key must return [] not crash."""
    _configure_llm(session)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_response("{}")

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm("Yumiko walked.", None)

    assert result == []


def test_extract_handles_null_glossary(session: Session) -> None:
    """Regression: 'glossary': null must return [] not crash."""
    _configure_llm(session)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_response('{"glossary": null}')

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm("Yumiko walked.", None)

    assert result == []


def test_extract_handles_non_list_glossary(session: Session) -> None:
    """Regression: 'glossary' as a string must return [] not crash."""
    _configure_llm(session)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_response('{"glossary": "not-a-list"}')

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm("Yumiko walked.", None)

    assert result == []
