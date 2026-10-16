"""Tests for stale-processing recovery and cancel fallback.

Two related bugs:
  1. When the backend restarts, projects stuck in PROCESSING never get
     cleared. They show a spinner forever and Stop does nothing.
  2. The cancel endpoint returns 409 when the pipeline isn't live,
     leaving the project in PROCESSING.

Fix:
  - On startup, mark any PROCESSING project as FAILED.
  - In the cancel endpoint, fall back to DB update if the pipeline
    isn't live (still cooperative, but always converges).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 — register ORM models
from app.core.db import Base, get_session
from app.main import create_app
from app.models.project import Project, ProjectStatus
from app.services import project_service


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


@pytest.fixture
def api_client() -> Iterator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record) -> None:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    app = create_app()

    def override_get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c, Session(engine) as s:
        # Yield both the client and a direct session for test manipulation
        yield c, s


# ---------------------------------------------------------------------------
# Bug 1: fail_stale_processing_projects
# ---------------------------------------------------------------------------


def test_fail_stale_processing_marks_all_processing(
    session: Session,
) -> None:
    """All PROCESSING projects must transition to FAILED."""
    p1 = Project(title="stuck-1", status=ProjectStatus.PROCESSING)
    p2 = Project(title="stuck-2", status=ProjectStatus.PROCESSING)
    p3 = Project(title="done", status=ProjectStatus.DONE)
    session.add_all([p1, p2, p3])
    session.commit()

    count = project_service.fail_stale_processing_projects(session)

    assert count == 2
    session.refresh(p1)
    session.refresh(p2)
    session.refresh(p3)
    assert p1.status == ProjectStatus.FAILED
    assert p2.status == ProjectStatus.FAILED
    assert p3.status == ProjectStatus.DONE  # untouched
    assert p1.error_message is not None
    assert "restart" in (p1.error_message or "").lower()


def test_fail_stale_processing_no_op_when_none(
    session: Session,
) -> None:
    """Returns 0 and doesn't crash when nothing is stuck."""
    p = Project(title="done", status=ProjectStatus.DONE)
    session.add(p)
    session.commit()

    count = project_service.fail_stale_processing_projects(session)

    assert count == 0


def test_fail_stale_processing_preserves_pending(
    session: Session,
) -> None:
    """PENDING projects must not be touched."""
    p = Project(title="pending", status=ProjectStatus.PENDING)
    session.add(p)
    session.commit()

    project_service.fail_stale_processing_projects(session)

    session.refresh(p)
    assert p.status == ProjectStatus.PENDING


# ---------------------------------------------------------------------------
# Bug 2: cancel fallback when pipeline isn't live
# ---------------------------------------------------------------------------


def test_cancel_no_live_pipeline_still_marks_cancelled(
    api_client: tuple[TestClient, Session],
) -> None:
    """If the pipeline isn't live, cancel must still update the DB
    to CANCELLED (not return 409)."""
    client, session = api_client

    # Create a project via the API
    r = client.post("/api/projects", json={"title": "cancel-test"})
    assert r.status_code in (200, 201), r.text
    project_id = r.json()["id"]

    # Manually set it to PROCESSING (no live pipeline exists)
    proj = session.get(Project, project_id)
    assert proj is not None
    proj.status = ProjectStatus.PROCESSING
    session.commit()

    # Now call cancel — no live pipeline, but must still work
    r = client.post(f"/api/process/{project_id}/cancel")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "cancelled"


def test_cancel_not_processing_still_409(
    api_client: tuple[TestClient, Session],
) -> None:
    """Cancel on a non-PROCESSING project must still return 409."""
    client, _session = api_client

    r = client.post("/api/projects", json={"title": "idle"})
    project_id = r.json()["id"]

    r = client.post(f"/api/process/{project_id}/cancel")
    assert r.status_code == 409
