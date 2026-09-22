"""Tests for AI-mode pipeline runner (mocked LLM)."""
from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import Project, ProjectStatus
from app.pipeline.glossary import CancelledError
from app.schemas.project import ProjectCreateEmpty
from app.schemas.source import TextSourceCreate
from app.services import pipeline_runner, project_service, source_service


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


def _mk_project_ai(session: Session) -> Project:
    p = project_service.create_empty(
        session,
        ProjectCreateEmpty(title="T", num_terms=10, processing_mode="ai"),
    )
    # Force a high density so both mock terms survive the cap.
    p.terms_per_1k_words = 500
    session.commit()

    source_service.add_text_source(
        session, p,
        TextSourceCreate(
            name="s1",
            text=(
                "Yumiko walked through Kagoshima. "
                "Yumiko smiled. Kagoshima was quiet."
            ),
        ),
    )
    session.refresh(p)
    return p


# New format: matches what extract_terms_llm returns after normalization
_FAKE_EXTRACTION = [
    {
        "term": "Yumiko",
        "persian_term": "یومیکو",
        "persian_alternatives": ["یومیکو"],
        "context": "Yumiko walked through Kagoshima.",
        "pos": "proper_noun",
        "category": "Character/Place Name",
        "persian_transliteration": "Yumiko",
        "translator_note": "نام شخصیت",
    },
    {
        "term": "Kagoshima",
        "persian_term": "کاگوشیما",
        "persian_alternatives": [],
        "context": "Yumiko walked through Kagoshima.",
        "pos": "proper_noun",
        "category": "Character/Place Name",
        "persian_transliteration": "Kagoshima",
        "translator_note": "نام شهر",
    },
]


def _make_fake_extract(captured_calls: list | None = None):
    """Build a fake extract that matches the new signature."""
    def fake_extract(text, meta, target_count=50, chunk_id="chunk-0"):
        if captured_calls is not None:
            captured_calls.append({
                "text": text,
                "metadata": meta,
                "target_count": target_count,
                "chunk_id": chunk_id,
            })
        return list(_FAKE_EXTRACTION)
    return fake_extract


def test_ai_pipeline_happy_path(session: Session) -> None:
    p = _mk_project_ai(session)

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=True,
    ), patch(
        "app.services.pipeline_runner.llm_client.extract_terms_llm",
        side_effect=_make_fake_extract(),
    ), patch(
        "app.services.pipeline_runner.llm_client.translate_many",
        return_value=["یومیکو", "کاگوشیما"],
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.DONE

    from app.models import GlossaryEntry
    entries = session.query(GlossaryEntry).all()
    assert len(entries) == 2
    terms = {e.english_term for e in entries}
    assert terms == {"Yumiko", "Kagoshima"}

    # Verify Persian terms present
    yumiko = next(e for e in entries if e.english_term == "Yumiko")
    assert yumiko.persian_term == "یومیکو"
    assert yumiko.pos == "proper_noun"
    assert yumiko.category == "Character/Place Name"
    assert yumiko.translator_note == "نام شخصیت"
    assert yumiko.persian_alternatives is not None

    # Definitions are empty in AI mode
    for e in entries:
        assert e.english_definition == ""
        assert e.persian_definition == ""
        assert e.source == "LLM"
        # Score derived from frequency
        assert 0.0 < e.score <= 1.0


def test_ai_pipeline_requires_llm_config(session: Session) -> None:
    p = _mk_project_ai(session)

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=False,
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.FAILED
    msg = (p.error_message or "").lower()
    assert "no llm" in msg or "api key" in msg


def test_ai_pipeline_handles_extraction_failure(session: Session) -> None:
    p = _mk_project_ai(session)

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=True,
    ), patch(
        "app.services.pipeline_runner.llm_client.extract_terms_llm",
        side_effect=RuntimeError("api down"),
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.FAILED
    assert "extract any terms" in (p.error_message or "").lower()


def test_ai_pipeline_empty_extraction_fails(session: Session) -> None:
    p = _mk_project_ai(session)

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=True,
    ), patch(
        "app.services.pipeline_runner.llm_client.extract_terms_llm",
        return_value=[],
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.FAILED
    assert "extract any terms" in (p.error_message or "").lower()


def test_ai_pipeline_uses_metadata(session: Session) -> None:
    """Verify metadata is passed to extract_terms_llm."""
    p = _mk_project_ai(session)
    metadata = {"book_metadata": {"title": "Love You"}}
    project_service.set_book_metadata(session, p, metadata)

    captured_calls: list = []

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=True,
    ), patch(
        "app.services.pipeline_runner.llm_client.extract_terms_llm",
        side_effect=_make_fake_extract(captured_calls),
    ), patch(
        "app.services.pipeline_runner.llm_client.translate_many",
        return_value=["", ""],
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    assert len(captured_calls) >= 1
    # The first call's metadata should match what we set
    assert captured_calls[0]["metadata"] == metadata


def test_ai_pipeline_cancellation(session: Session) -> None:
    p = _mk_project_ai(session)

    def cancel_now(*args, **kwargs):
        raise CancelledError("test cancel")

    with patch(
        "app.services.pipeline_runner.llm_client.is_configured",
        return_value=True,
    ), patch(
        "app.services.pipeline_runner.llm_client.extract_terms_llm",
        side_effect=cancel_now,
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.CANCELLED


# ---------------------------------------------------------------------------
# Chunking tests
# ---------------------------------------------------------------------------


def test_split_into_chunks_single() -> None:
    text = "one two three four"
    chunks = pipeline_runner._split_into_chunks(text, 10)
    assert chunks == [text]


def test_split_into_chunks_multiple() -> None:
    text = " ".join(f"w{i}" for i in range(10))
    chunks = pipeline_runner._split_into_chunks(text, 3)
    assert len(chunks) == 4
    assert chunks[0] == "w0 w1 w2"
    assert chunks[3] == "w9"


def test_split_into_chunks_empty() -> None:
    assert pipeline_runner._split_into_chunks("", 10) == []
    assert pipeline_runner._split_into_chunks("   ", 10) == []