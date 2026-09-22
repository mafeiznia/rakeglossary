"""Tests for the export endpoints."""
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
        with Session(engine) as s:
            p = Project(title="Book")
            s.add(p)
            s.commit()
            s.add(GlossaryEntry(
                project_id=p.id, english_term="DNA",
                persian_term="دی‌ان‌ای", score=0.9,
                english_definition="A molecule.",
                persian_definition="یک مولکول.",
            ))
            s.commit()
            c.project_id = p.id  # type: ignore[attr-defined]
        yield c


def test_export_csv(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/export/{pid}/csv")
    assert r.status_code == 200
    assert b"English Term" in r.content
    assert "DNA".encode() in r.content


def test_export_xlsx(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/export/{pid}/xlsx")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


def test_export_tbx(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/export/{pid}/tbx")
    assert r.status_code == 200
    assert b"<tbx" in r.content


def test_export_unsupported_format(client: TestClient) -> None:
    pid = client.project_id  # type: ignore[attr-defined]
    r = client.get(f"/api/export/{pid}/pdf")
    assert r.status_code == 400


def test_export_missing_project(client: TestClient) -> None:
    r = client.get("/api/export/nope/csv")
    assert r.status_code == 404