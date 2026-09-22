"""Tests for the projects API endpoints."""
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
        yield c


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_project_empty(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "My Book"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "My Book"
    assert body["source_count"] == 0
    assert body["word_count"] == 0
    assert body["status"] == "pending"
    assert body["sources"] == []


def test_create_project_rejects_empty_title(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "   "})
    assert r.status_code == 422


def test_list_projects(client: TestClient) -> None:
    for i in range(3):
        client.post("/api/projects", json={"title": f"T{i}"})
    r = client.get("/api/projects")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3


def test_get_project(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "T"})
    pid = r.json()["id"]

    r2 = client.get(f"/api/projects/{pid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == pid


def test_get_missing_project(client: TestClient) -> None:
    r = client.get("/api/projects/does-not-exist")
    assert r.status_code == 404


def test_update_project(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "Old"})
    pid = r.json()["id"]

    r2 = client.patch(
        f"/api/projects/{pid}",
        json={"title": "New", "num_terms": 20},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["title"] == "New"
    assert body["num_terms"] == 20


def test_delete_project(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "T"})
    pid = r.json()["id"]

    r2 = client.delete(f"/api/projects/{pid}")
    assert r2.status_code == 204

    r3 = client.get(f"/api/projects/{pid}")
    assert r3.status_code == 404
    
# ---------------------------------------------------------------------------
# Book metadata
# ---------------------------------------------------------------------------


def test_set_and_get_book_metadata(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "Book A"})
    pid = r.json()["id"]

    metadata = {
        "book_metadata": {
            "title": "The Great Novel",
            "author": "Jane Doe",
            "publication_year": 2020,
        },
        "content_classification": {
            "primary_genre": "Historical Fiction",
            "main_themes": ["love", "war"],
        },
    }
    r2 = client.put(f"/api/projects/{pid}/metadata", json=metadata)
    assert r2.status_code == 200
    body = r2.json()
    assert body["book_metadata"]["book_metadata"]["title"] == "The Great Novel"
    assert (
        body["book_metadata"]["content_classification"]["primary_genre"]
        == "Historical Fiction"
    )

    r3 = client.get(f"/api/projects/{pid}")
    assert r3.json()["book_metadata"]["book_metadata"]["author"] == "Jane Doe"


def test_clear_book_metadata(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "Book B"})
    pid = r.json()["id"]

    client.put(
        f"/api/projects/{pid}/metadata",
        json={"book_metadata": {"title": "X"}},
    )
    r2 = client.delete(f"/api/projects/{pid}/metadata")
    assert r2.status_code == 200
    assert r2.json()["book_metadata"] is None


def test_book_metadata_is_none_initially(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "Book C"})
    pid = r.json()["id"]

    r2 = client.get(f"/api/projects/{pid}")
    assert r2.json()["book_metadata"] is None


def test_book_metadata_accepts_partial_structure(client: TestClient) -> None:
    r = client.post("/api/projects", json={"title": "Book D"})
    pid = r.json()["id"]

    client.put(
        f"/api/projects/{pid}/metadata",
        json={"book_metadata": {"title": "Just a Title"}},
    )
    r2 = client.get(f"/api/projects/{pid}")
    assert r2.json()["book_metadata"]["book_metadata"]["title"] == "Just a Title"
    assert "content_classification" not in r2.json()["book_metadata"]    