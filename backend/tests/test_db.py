"""Tests for the database foundation and ORM models."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import (
    GlossaryEntry,
    Project,
    ProjectSource,
    ProjectStatus,
    Setting,
    SourceType,
)


@pytest.fixture
def session() -> Iterator[Session]:
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
        yield s


def test_create_project(session: Session) -> None:
    p = Project(title="Test")
    session.add(p)
    session.commit()

    assert p.id is not None
    assert p.status == ProjectStatus.PENDING
    assert p.num_terms == 30
    assert p.word_count == 0
    assert p.source_count == 0
    assert p.created_at is not None


def test_create_file_source(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    src = ProjectSource(
        project_id=p.id,
        source_type=SourceType.FILE,
        path="C:/books/ch1.pdf",
        original_name="ch1.pdf",
        word_count=100,
        order_index=0,
    )
    session.add(src)
    session.commit()

    assert src.id is not None
    assert src.included is True
    assert len(p.sources) == 1


def test_create_text_source(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    src = ProjectSource(
        project_id=p.id,
        source_type=SourceType.TEXT,
        text_content="Hello world",
        original_name="snippet",
        word_count=2,
    )
    session.add(src)
    session.commit()

    assert src.text_content == "Hello world"
    assert src.path is None


def test_sources_ordered_by_order_index(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    for i, name in enumerate(["c", "a", "b"]):
        session.add(ProjectSource(
            project_id=p.id,
            source_type=SourceType.TEXT,
            text_content=name,
            original_name=name,
            order_index=i,
        ))
    session.commit()

    session.refresh(p)
    names = [s.original_name for s in p.sources]
    assert names == ["c", "a", "b"]


def test_cascade_delete_project_removes_sources(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    for name in ("a", "b", "c"):
        session.add(ProjectSource(
            project_id=p.id,
            source_type=SourceType.TEXT,
            text_content=name,
            original_name=name,
        ))
    session.commit()

    assert session.query(ProjectSource).count() == 3
    session.delete(p)
    session.commit()
    assert session.query(ProjectSource).count() == 0


def test_create_glossary_entry(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    e = GlossaryEntry(
        project_id=p.id,
        english_term="DNA",
        persian_term="دی‌ان‌ای",
        english_definition="A molecule.",
        score=0.9,
    )
    session.add(e)
    session.commit()

    assert e.id is not None
    assert e.project.id == p.id
    assert len(p.entries) == 1
    assert e.is_edited is False


def test_glossary_cascade_delete(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    for term in ("AI", "ML", "DNA"):
        session.add(GlossaryEntry(project_id=p.id, english_term=term, score=0.5))
    session.commit()
    assert session.query(GlossaryEntry).count() == 3

    session.delete(p)
    session.commit()
    assert session.query(GlossaryEntry).count() == 0


def test_entries_ordered_by_score_desc(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    for term, score in [("low", 0.1), ("high", 0.9), ("mid", 0.5)]:
        session.add(GlossaryEntry(project_id=p.id, english_term=term, score=score))
    session.commit()

    session.refresh(p)
    terms = [e.english_term for e in p.entries]
    assert terms == ["high", "mid", "low"]


def test_setting_roundtrip(session: Session) -> None:
    s = Setting(key="theme", value='"dark"')
    session.add(s)
    session.commit()

    fetched = session.get(Setting, "theme")
    assert fetched is not None
    assert fetched.value == '"dark"'


def test_status_enum_values(session: Session) -> None:
    p = Project(title="T")
    session.add(p)
    session.commit()

    for status in (
        ProjectStatus.PROCESSING,
        ProjectStatus.DONE,
        ProjectStatus.FAILED,
        ProjectStatus.CANCELLED,
    ):
        p.status = status
        session.commit()
        session.refresh(p)
        assert p.status == status