"""Tests for project_service."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import Project, ProjectStatus
from app.schemas.project import ProcessRequest, ProjectCreateEmpty
from app.services import project_service


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


def test_create_empty(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="Book"))
    assert p.id
    assert p.title == "Book"
    assert p.status == ProjectStatus.PENDING
    assert p.word_count == 0
    assert p.source_count == 0


def test_create_empty_with_options(session: Session) -> None:
    p = project_service.create_empty(
        session,
        ProjectCreateEmpty(title="T", num_terms=12, translate_terms=False),
    )
    assert p.num_terms == 12
    assert p.translate_terms is False


def test_list_paginated(session: Session) -> None:
    for i in range(7):
        project_service.create_empty(session, ProjectCreateEmpty(title=f"T{i}"))
    page1, total = project_service.list_paginated(session, page=1, page_size=3)
    page2, _ = project_service.list_paginated(session, page=2, page_size=3)

    assert total == 7
    assert len(page1) == 3
    assert len(page2) == 3
    assert page1[0].title == "T6"


def test_state_transitions(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))

    project_service.mark_processing(session, p)
    assert p.status == ProjectStatus.PROCESSING
    assert p.started_at is not None

    project_service.mark_done(session, p)
    assert p.status == ProjectStatus.DONE
    assert p.finished_at is not None


def test_mark_failed_sets_error(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    project_service.mark_failed(session, p, "boom")
    assert p.status == ProjectStatus.FAILED
    assert p.error_message == "boom"


def test_mark_cancelled(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    project_service.mark_cancelled(session, p, "stopped")
    assert p.status == ProjectStatus.CANCELLED
    assert p.error_message == "stopped"


def test_apply_process_options(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    opts = ProcessRequest(num_terms=12, translate_terms=False, use_yake=False)
    project_service.apply_process_options(session, p, opts)

    assert p.num_terms == 12
    assert p.translate_terms is False
    assert p.use_yake is False


def test_delete_project(session: Session) -> None:
    p = project_service.create_empty(session, ProjectCreateEmpty(title="T"))
    pid = p.id
    project_service.delete(session, p)
    assert project_service.get(session, pid) is None