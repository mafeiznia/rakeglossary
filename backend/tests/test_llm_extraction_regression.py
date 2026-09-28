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


# ---------------------------------------------------------------------------
# Bug 8: extraction prompt omits some metadata fields
# ---------------------------------------------------------------------------


def test_extraction_prompt_includes_all_metadata_fields() -> None:
    """Regression: _EXTRACTION_SYSTEM_FULL must surface every metadata field
    that _extract_metadata_fields produces, so the LLM can use them.

    Currently missing: sub_genres, main_themes, target_audience,
    reading_level, vocabulary_complexity, cultural_context.
    """
    metadata = {
        "book_metadata": {"title": "The Novel", "author": "Jane Doe"},
        "content_classification": {
            "primary_genre": "Historical Fiction",
            "sub_genres": ["Romance", "War"],
            "main_themes": ["love", "loss"],
            "setting": {"time_period": "WWII", "location": "Paris"},
        },
        "audience_analysis": {
            "target_audience": "Adults",
            "reading_level": "Intermediate",
        },
        "stylistic_analysis": {
            "vocabulary_complexity": "Everyday",
            "overall_tone": "Melancholic",
            "writing_style": "Descriptive",
        },
        "translation_guidelines": {
            "cultural_context": "European history",
            "key_terminology": [{"term": "resistance", "suggested_translation": "مقاومت"}],
        },
    }
    prompt, kind = llm_client._build_extraction_prompt(metadata, 40, "c-1")

    assert kind == "full"

    # Fields already in the prompt — must not regress:
    assert "The Novel" in prompt
    assert "Jane Doe" in prompt
    assert "Historical Fiction" in prompt
    assert "WWII" in prompt
    assert "Paris" in prompt

    # Fields that _extract_metadata_fields produces but the prompt omits:
    assert "Romance" in prompt, "sub_genres missing from prompt"
    assert "War" in prompt, "sub_genres missing from prompt"
    assert "love" in prompt, "main_themes missing from prompt"
    assert "loss" in prompt, "main_themes missing from prompt"
    assert "Adults" in prompt, "target_audience missing from prompt"
    assert "Intermediate" in prompt, "reading_level missing from prompt"
    assert "Everyday" in prompt, "vocabulary_complexity missing from prompt"
    assert "European history" in prompt, "cultural_context missing from prompt"
