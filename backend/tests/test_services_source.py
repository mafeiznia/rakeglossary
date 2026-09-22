"""Tests for source_service."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import Project, ProjectSource, SourceType
from app.schemas.project import ProjectCreateEmpty
from app.schemas.source import ProjectSourceUpdate, TextSourceCreate
from app.services import project_service, source_service


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


@pytest.fixture
def project(session: Session) -> Project:
    return project_service.create_empty(session, ProjectCreateEmpty(title="T"))


def test_add_text_source(session: Session, project: Project) -> None:
    src = source_service.add_text_source(
        session,
        project,
        TextSourceCreate(name="Chapter 1", text="one two three four"),
    )
    assert src.id
    assert src.source_type == SourceType.TEXT
    assert src.word_count == 4
    assert src.included is True


def test_add_text_source_updates_aggregates(
    session: Session, project: Project
) -> None:
    source_service.add_text_source(
        session, project, TextSourceCreate(name="a", text="a b c")
    )
    source_service.add_text_source(
        session, project, TextSourceCreate(name="b", text="d e")
    )
    session.refresh(project)
    assert project.source_count == 2
    assert project.word_count == 5


def test_add_file_source(session: Session, project: Project, tmp_path: Path) -> None:
    # small text file disguised as a valid extension
    content = b"alpha beta gamma"
    src = source_service.add_file_source(
        session, project, content, "chapter1.txt"
    )
    assert src.id
    assert src.source_type == SourceType.FILE
    assert src.path is not None
    assert src.word_count == 3
    assert Path(src.path).exists()


def test_order_index_increments(session: Session, project: Project) -> None:
    a = source_service.add_text_source(
        session, project, TextSourceCreate(name="a", text="x")
    )
    b = source_service.add_text_source(
        session, project, TextSourceCreate(name="b", text="y")
    )
    c = source_service.add_text_source(
        session, project, TextSourceCreate(name="c", text="z")
    )
    assert a.order_index < b.order_index < c.order_index


def test_list_for_project(session: Session, project: Project) -> None:
    for name in ("a", "b", "c"):
        source_service.add_text_source(
            session, project, TextSourceCreate(name=name, text="x")
        )
    rows = source_service.list_for_project(session, project.id)
    assert [r.original_name for r in rows] == ["a", "b", "c"]


def test_update_source_toggle_included(session: Session, project: Project) -> None:
    src = source_service.add_text_source(
        session, project, TextSourceCreate(name="a", text="one two three")
    )
    session.refresh(project)
    assert project.word_count == 3

    updated = source_service.update_source(
        session, src, ProjectSourceUpdate(included=False)
    )
    assert updated.included is False
    session.refresh(project)
    assert project.word_count == 0  # excluded sources not counted


def test_update_source_rename(session: Session, project: Project) -> None:
    src = source_service.add_text_source(
        session, project, TextSourceCreate(name="old", text="x")
    )
    updated = source_service.update_source(
        session, src, ProjectSourceUpdate(original_name="new")
    )
    assert updated.original_name == "new"


def test_delete_source(session: Session, project: Project, tmp_path: Path) -> None:
    src = source_service.add_file_source(
        session, project, b"hello world", "sample.txt"
    )
    file_path = src.path
    assert Path(file_path).exists()

    source_service.delete_source(session, src)
    assert session.query(ProjectSource).count() == 0
    assert not Path(file_path).exists()


def test_delete_cascades_with_project(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    for name in ("a", "b"):
        source_service.add_text_source(
            session, p, TextSourceCreate(name=name, text="x")
        )
    assert session.query(ProjectSource).count() == 2

    project_service.delete(session, p)
    assert session.query(ProjectSource).count() == 0