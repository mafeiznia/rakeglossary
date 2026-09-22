"""Tests for glossary_service."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import GlossaryEntry, Project
from app.pipeline.glossary import GlossaryEntry as PipelineEntry
from app.schemas.glossary import GlossaryEntryUpdate
from app.services import glossary_service


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


def _mk_project(session: Session) -> Project:
    p = Project(title="T")
    session.add(p)
    session.commit()
    return p


def _mk_pipeline_entries() -> list[PipelineEntry]:
    return [
        PipelineEntry(
            english_term="DNA", persian_term="دی‌ان‌ای",
            english_definition="A molecule.", persian_definition="یک مولکول.",
            source="In-Text", score=0.9, frequency=3, context="DNA is...",
        ),
        PipelineEntry(
            english_term="AI", persian_term="هوش مصنوعی",
            english_definition="A field.", persian_definition="یک رشته.",
            source="Wikipedia", score=0.5, frequency=1, context="AI is...",
        ),
    ]


def test_replace_entries_inserts(session: Session) -> None:
    p = _mk_project(session)
    rows = glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    assert len(rows) == 2
    assert session.query(GlossaryEntry).count() == 2


def test_replace_entries_deletes_old(session: Session) -> None:
    p = _mk_project(session)
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries()[:1])
    assert session.query(GlossaryEntry).count() == 1


def test_list_for_project_ordered_by_score(session: Session) -> None:
    p = _mk_project(session)
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    rows = glossary_service.list_for_project(session, p.id)
    assert [r.english_term for r in rows] == ["DNA", "AI"]


def test_update_marks_edited(session: Session) -> None:
    p = _mk_project(session)
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    entry = glossary_service.list_for_project(session, p.id)[0]

    glossary_service.update(
        session, entry, GlossaryEntryUpdate(persian_term="مولکول")
    )
    assert entry.persian_term == "مولکول"
    assert entry.is_edited is True


def test_update_respects_explicit_is_edited(session: Session) -> None:
    p = _mk_project(session)
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    entry = glossary_service.list_for_project(session, p.id)[0]

    glossary_service.update(session, entry, GlossaryEntryUpdate(is_edited=False))
    assert entry.is_edited is False


def test_delete_entry(session: Session) -> None:
    p = _mk_project(session)
    glossary_service.replace_entries(session, p.id, _mk_pipeline_entries())
    entry = glossary_service.list_for_project(session, p.id)[0]
    glossary_service.delete_entry(session, entry)
    assert session.query(GlossaryEntry).count() == 1