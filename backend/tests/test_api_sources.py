"""Tests for the project sources API endpoints."""
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


def _mk_project(client: TestClient, title: str = "T") -> str:
    r = client.post("/api/projects", json={"title": title})
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Text sources
# ---------------------------------------------------------------------------


def test_add_text_source(client: TestClient) -> None:
    pid = _mk_project(client)
    r = client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "Chapter 1", "text": "one two three"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["source_type"] == "text"
    assert body["word_count"] == 3
    assert body["included"] is True


def test_add_text_updates_project_aggregates(client: TestClient) -> None:
    pid = _mk_project(client)
    client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "a", "text": "a b c"},
    )
    client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "b", "text": "d e"},
    )
    r = client.get(f"/api/projects/{pid}")
    body = r.json()
    assert body["source_count"] == 2
    assert body["word_count"] == 5


# ---------------------------------------------------------------------------
# File sources
# ---------------------------------------------------------------------------


def test_upload_single_file(client: TestClient) -> None:
    pid = _mk_project(client)
    files = {"files": ("chapter1.txt", b"alpha beta gamma delta", "text/plain")}
    r = client.post(f"/api/projects/{pid}/sources/upload", files=files)
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body) == 1
    assert body[0]["source_type"] == "file"
    assert body[0]["word_count"] == 4


def test_upload_multiple_files(client: TestClient) -> None:
    pid = _mk_project(client)
    files = [
        ("files", ("c.txt", b"c c c", "text/plain")),
        ("files", ("a.txt", b"a a", "text/plain")),
        ("files", ("b.txt", b"b", "text/plain")),
    ]
    r = client.post(f"/api/projects/{pid}/sources/upload", files=files)
    assert r.status_code == 201
    body = r.json()
    assert len(body) == 3
    # alphabetical order: a.txt, b.txt, c.txt
    names = [s["original_name"] for s in body]
    assert names == ["a.txt", "b.txt", "c.txt"]


def test_upload_rejects_bad_extension(client: TestClient) -> None:
    pid = _mk_project(client)
    files = {"files": ("evil.exe", b"binary", "application/octet-stream")}
    r = client.post(f"/api/projects/{pid}/sources/upload", files=files)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# List / update / delete
# ---------------------------------------------------------------------------


def test_list_sources(client: TestClient) -> None:
    pid = _mk_project(client)
    for name in ("a", "b", "c"):
        client.post(
            f"/api/projects/{pid}/sources/text",
            json={"name": name, "text": "x"},
        )
    r = client.get(f"/api/projects/{pid}/sources")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_update_source_toggle_included(client: TestClient) -> None:
    pid = _mk_project(client)
    r = client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "a", "text": "x y z"},
    )
    sid = r.json()["id"]

    r2 = client.patch(
        f"/api/projects/{pid}/sources/{sid}",
        json={"included": False},
    )
    assert r2.status_code == 200
    assert r2.json()["included"] is False

    # project aggregate updated
    r3 = client.get(f"/api/projects/{pid}")
    assert r3.json()["word_count"] == 0


def test_delete_source(client: TestClient) -> None:
    pid = _mk_project(client)
    r = client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "a", "text": "x"},
    )
    sid = r.json()["id"]

    r2 = client.delete(f"/api/projects/{pid}/sources/{sid}")
    assert r2.status_code == 204

    r3 = client.get(f"/api/projects/{pid}/sources")
    assert r3.json() == []


def test_delete_missing_source_returns_404(client: TestClient) -> None:
    pid = _mk_project(client)
    r = client.delete(f"/api/projects/{pid}/sources/9999")
    assert r.status_code == 404