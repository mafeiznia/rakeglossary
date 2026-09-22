"""Tests for LLM-based term extraction (mocked)."""
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
        import app.pipeline.llm_client as llm_module_imported
        monkeypatch.setattr(
            llm_module_imported, "SessionLocal", lambda: _SameSession(s)
        )
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
# Metadata field extraction
# ---------------------------------------------------------------------------


def test_extract_metadata_fields_empty() -> None:
    fields = llm_client._extract_metadata_fields(None)
    assert fields["title"] == ""
    assert fields["primary_genre"] == ""
    assert fields["authorial_tone"] == ""


def test_extract_metadata_fields_full() -> None:
    metadata = {
        "book_metadata": {
            "title": "The Novel",
            "author": "Jane Doe",
        },
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
            "key_terminology": [
                {"term": "résistance", "suggested_translation": "مقاومت"}
            ],
        },
    }
    fields = llm_client._extract_metadata_fields(metadata)
    assert fields["title"] == "The Novel"
    assert fields["primary_genre"] == "Historical Fiction"
    assert "Romance" in fields["sub_genres"]
    assert fields["time_period"] == "WWII"
    assert "résistance" in fields["key_terminology"]
    # authorial_tone combined from tone + style
    assert "Melancholic" in fields["authorial_tone"]
    assert "Descriptive" in fields["authorial_tone"]


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def test_build_prompt_minimal_when_no_metadata() -> None:
    prompt, kind = llm_client._build_extraction_prompt(None, 50, "chunk-0")
    assert kind == "minimal"
    assert "50" in prompt
    assert "chunk-0" in prompt


def test_build_prompt_minimal_when_metadata_empty() -> None:
    prompt, kind = llm_client._build_extraction_prompt({}, 30, "chunk-1")
    assert kind == "minimal"
    assert "chunk-1" in prompt


def test_build_prompt_full_when_metadata_present() -> None:
    metadata = {"book_metadata": {"title": "My Book"}}
    prompt, kind = llm_client._build_extraction_prompt(metadata, 40, "c-1")
    assert kind == "full"
    assert "My Book" in prompt
    assert "40" in prompt
    assert "c-1" in prompt


def test_strip_markdown_fences() -> None:
    assert llm_client._strip_markdown_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert llm_client._strip_markdown_fences('```\n{"a": 1}\n```') == '{"a": 1}'
    assert llm_client._strip_markdown_fences('{"a": 1}') == '{"a": 1}'


# ---------------------------------------------------------------------------
# Term-in-text validation
# ---------------------------------------------------------------------------


def test_term_in_text_exact() -> None:
    assert llm_client._term_in_text("Yumiko", "Yumiko walked home.")
    assert llm_client._term_in_text("yumiko", "Yumiko walked home.")
    assert llm_client._term_in_text("Yumiko", "yumiko walked home.")


def test_term_in_text_not_present() -> None:
    assert not llm_client._term_in_text("Kagoshima", "Yumiko walked home.")
    assert not llm_client._term_in_text("", "anything")
    assert not llm_client._term_in_text("term", "")


def test_term_in_text_word_boundary() -> None:
    # "cat" should not match "category"
    assert not llm_client._term_in_text("cat", "This is a category.")
    assert llm_client._term_in_text("cat", "The cat is here.")


# ---------------------------------------------------------------------------
# extract_terms_llm (mocked API)
# ---------------------------------------------------------------------------


def test_extract_returns_empty_for_empty_text(session: Session) -> None:
    assert llm_client.extract_terms_llm("", None) == []
    assert llm_client.extract_terms_llm("   ", None) == []


def test_extract_parses_valid_response(session: Session) -> None:
    _configure_llm(session)
    source = "Yumiko walked through Kagoshima yesterday."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "pos": "proper_noun", '
        '"category": "Character/Place Name", '
        '"persian_primary": "یومیکو", "persian_alternatives": ["یومیکو"], '
        '"context_sentence": "Yumiko walked through Kagoshima yesterday."},'
        '{"source_term": "Kagoshima", "pos": "proper_noun", '
        '"category": "Character/Place Name", '
        '"persian_primary": "کاگوشیما", "persian_alternatives": [], '
        '"context_sentence": "Yumiko walked through Kagoshima yesterday."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None, target_count=5)

    assert len(result) == 2
    assert result[0]["term"] == "Yumiko"
    assert result[0]["persian_term"] == "یومیکو"
    assert result[0]["pos"] == "proper_noun"
    assert result[1]["term"] == "Kagoshima"


def test_extract_rejects_hallucinated_terms(session: Session) -> None:
    """Terms not present verbatim in the source should be skipped."""
    _configure_llm(session)
    source = "Yumiko walked home."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "Yumiko walked home."},'
        '{"source_term": "Cultural references", "persian_primary": "ارجاعات", '
        '"context_sentence": "Yumiko walked home."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    # "Cultural references" is hallucinated — should be dropped
    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"


def test_extract_drops_mismatched_context(session: Session) -> None:
    """If context doesn't contain the term, it should be dropped."""
    _configure_llm(session)
    source = "Yumiko walked home. She felt peace."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "She felt peace."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"
    # Context should be dropped because it doesn't contain "Yumiko"
    assert result[0]["context"] == ""


def test_extract_handles_markdown_fences(session: Session) -> None:
    _configure_llm(session)
    source = "Yumiko walked."
    response = _mock_response(
        '```json\n'
        '{"glossary": [{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "Yumiko walked."}]}\n'
        "```"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"


def test_extract_handles_invalid_json(session: Session) -> None:
    _configure_llm(session)
    response = _mock_response("not json at all")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm("Yumiko walked.", None)

    assert result == []


def test_extract_handles_api_error(session: Session) -> None:
    _configure_llm(session)
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("network down")

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm("Yumiko walked.", None)

    assert result == []


def test_extract_deduplicates_terms(session: Session) -> None:
    _configure_llm(session)
    source = "Yumiko and Yumiko."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "Yumiko and Yumiko."},'
        '{"source_term": "yumiko", "persian_primary": "تکراری", '
        '"context_sentence": "Yumiko and Yumiko."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"


def test_extract_skips_missing_fields(session: Session) -> None:
    _configure_llm(session)
    source = "Yumiko walked home."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "Yumiko walked home."},'
        '{"source_term": "", "persian_primary": "no term"},'
        '{"persian_primary": "no source_term"},'
        '{"not_a_term": "x"}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"


def test_extract_parses_context_field(session: Session) -> None:
    _configure_llm(session)
    source = "She felt deep empathy for the stranger."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "empathy", "persian_primary": "همدلی", '
        '"context_sentence": "She felt deep empathy for the stranger."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["context"] == "She felt deep empathy for the stranger."


def test_extract_truncates_long_context(session: Session) -> None:
    _configure_llm(session)
    # Context longer than 250 chars, but contains the term
    term = "Yumiko"
    long_ctx = "Yumiko " + ("x" * 300)
    source = long_ctx
    response = _mock_response(
        '{"glossary": [{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"context_sentence": "' + long_ctx + '"}]}'
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert len(result[0]["context"]) <= 253
    assert result[0]["context"].endswith("...")


def test_extract_handles_missing_context_field(session: Session) -> None:
    """If LLM omits context, we should still extract the term."""
    _configure_llm(session)
    source = "Yumiko walked home."
    response = _mock_response(
        '{"glossary": [{"source_term": "Yumiko", "persian_primary": "یومیکو"}]}'
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    assert result[0]["term"] == "Yumiko"
    assert result[0]["context"] == ""


def test_extract_parses_all_ai_extras(session: Session) -> None:
    """Verify pos, category, alternatives, note, transliteration are parsed."""
    _configure_llm(session)
    source = "Yumiko walked through Kagoshima yesterday."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", '
        '"pos": "proper_noun", '
        '"category": "Character/Place Name", '
        '"persian_primary": "یومیکو", '
        '"persian_transliteration": "Yumiko", '
        '"persian_alternatives": ["یومیکو سان", "خانم یومیکو"], '
        '"context_sentence": "Yumiko walked through Kagoshima yesterday.", '
        '"translator_note": "نام شخصیت اصلی"}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result) == 1
    r = result[0]
    assert r["term"] == "Yumiko"
    assert r["persian_term"] == "یومیکو"
    assert r["pos"] == "proper_noun"
    assert r["category"] == "Character/Place Name"
    assert r["persian_transliteration"] == "Yumiko"
    assert r["translator_note"] == "نام شخصیت اصلی"
    assert "یومیکو سان" in r["persian_alternatives"]
    assert "خانم یومیکو" in r["persian_alternatives"]


def test_extract_limits_alternatives_to_three(session: Session) -> None:
    _configure_llm(session)
    source = "Yumiko walked home."
    response = _mock_response(
        '{"glossary": ['
        '{"source_term": "Yumiko", "persian_primary": "یومیکو", '
        '"persian_alternatives": ["a", "b", "c", "d", "e"], '
        '"context_sentence": "Yumiko walked home."}'
        "]}"
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response

    with patch("openai.OpenAI", return_value=mock_client):
        result = llm_client.extract_terms_llm(source, None)

    assert len(result[0]["persian_alternatives"]) == 3