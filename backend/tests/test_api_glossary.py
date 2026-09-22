"""Tests for the glossary API endpoints."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.db import Base, get_session
from app.main import create_app
from app.models import GlossaryEntry, Project


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite:///:memory:", future=True,
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
    with TestClient(app) as c:
        # seed a project + two entries
        with Session(engine) as s:
            p = Project(title="P")
            s.add(p)
            s.commit()
            s.add_all([
                GlossaryEntry(project_id=p.id, english_term="DNA", score=0.9),
                GlossaryEntry(project_id=p.id, english_term="AI", score=0.5),
            ])
            s.commit()
            c.project_id = p.id  # type: ignore[attr-defined]
        yield c


def test_get_glossary(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/projects/{pid}/glossary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["entries"][0]["english_term"] == "DNA"


def test_get_glossary_missing_project(client: TestClient) -> None:
    r = client.get("/api/projects/nope/glossary")
    assert r.status_code == 404


def test_update_entry_marks_edited(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/projects/{pid}/glossary")
    eid = r.json()["entries"][0]["id"]

    r2 = client.patch(
        f"/api/glossary/{eid}",
        json={"persian_term": "دی‌ان‌ای", "persian_definition": "یک مولکول"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["persian_term"] == "دی‌ان‌ای"
    assert body["is_edited"] is True


def test_update_missing_entry(client: TestClient) -> None:
    r = client.patch("/api/glossary/9999", json={"persian_term": "x"})
    assert r.status_code == 404


def test_delete_entry(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/projects/{pid}/glossary")
    eid = r.json()["entries"][0]["id"]

    r2 = client.delete(f"/api/glossary/{eid}")
    assert r2.status_code == 204

    r3 = client.get(f"/api/projects/{pid}/glossary")
    assert r3.json()["total"] == 1