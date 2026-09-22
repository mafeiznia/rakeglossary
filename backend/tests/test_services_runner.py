"""Tests for pipeline_runner with per-source processing."""
from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import Project, ProjectStatus
from app.pipeline.glossary import CancelledError
from app.pipeline.glossary import GlossaryEntry as PipelineEntry
from app.pipeline.nlp import Keyword
from app.schemas.project import ProjectCreateEmpty
from app.schemas.source import ProjectSourceUpdate, TextSourceCreate
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


def _mk_project_with_source(session: Session) -> Project:
    p = project_service.create_empty(
        session, ProjectCreateEmpty(title="T", num_terms=5)
    )
    source_service.add_text_source(
        session, p,
        TextSourceCreate(
            name="s1",
            text="hello world. hello again. hello universe.",
        ),
    )
    session.refresh(p)
    return p


def test_runner_success_path(session: Session) -> None:
    """Full pipeline with mocked NLP so no real extraction runs."""
    p = _mk_project_with_source(session)

    fake_keywords = [Keyword(term="hello", score=0.9)]

    with patch(
        "app.services.pipeline_runner.extract_keywords",
        return_value=fake_keywords,
    ), patch(
        "app.services.pipeline_runner.resolve_classic",
    ) as mock_resolve, patch(
        "app.services.pipeline_runner.translate_many",
        return_value=["ترجمه"],
    ):
        from app.pipeline.definitions import DefinitionResult, DefinitionSource
        mock_resolve.return_value = DefinitionResult(
            text="A greeting.", source=DefinitionSource.IN_TEXT,
        )

        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.DONE
    assert p.finished_at is not None

    from app.models import GlossaryEntry
    assert session.query(GlossaryEntry).count() == 1


def test_runner_failure_path(session: Session) -> None:
    p = _mk_project_with_source(session)
    with patch(
        "app.services.pipeline_runner.extract_keywords",
        side_effect=RuntimeError("boom"),
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.FAILED
    assert "boom" in (p.error_message or "")


def test_runner_no_sources_fails(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.FAILED
    assert "no usable source" in (p.error_message or "").lower()


def test_runner_skips_excluded_sources(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    source_service.add_text_source(
        session, p, TextSourceCreate(name="s1", text="included text here")
    )
    s2 = source_service.add_text_source(
        session, p, TextSourceCreate(name="s2", text="excluded text here")
    )
    source_service.update_source(session, s2, ProjectSourceUpdate(included=False))

    captured_texts: list[str] = []

    def fake_extract(text, **kwargs):
        captured_texts.append(text)
        return []

    with patch(
        "app.services.pipeline_runner.extract_keywords",
        side_effect=fake_extract,
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    # Only the included source should have been extracted
    assert any("included" in t for t in captured_texts)
    assert not any("excluded" in t for t in captured_texts)


def test_runner_cancellation(session: Session) -> None:
    """Cancellation raised inside extract_keywords aborts the pipeline."""
    p = _mk_project_with_source(session)

    def cancel_now(*args, **kwargs):
        raise CancelledError("test cancel")

    with patch(
        "app.services.pipeline_runner.extract_keywords",
        side_effect=cancel_now,
    ):
        pipeline_runner._run_pipeline_sync(p.id, session=session)

    session.refresh(p)
    assert p.status == ProjectStatus.CANCELLED