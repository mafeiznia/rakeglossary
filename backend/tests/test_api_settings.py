"""Tests for the settings API + stopwords endpoints."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

from app import models  # noqa: F401 — register ORM models
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


def test_stopwords_empty_initially(client: TestClient) -> None:
    r = client.get("/api/settings/stopwords")
    assert r.status_code == 200
    body = r.json()
    assert body["words"] == []
    assert body["total"] == 0


def test_add_stopword(client: TestClient) -> None:
    r = client.post("/api/settings/stopwords", json={"word": "  Happened  "})
    assert r.status_code == 201
    body = r.json()
    assert body["words"] == ["happened"]
    assert body["total"] == 1


def test_add_duplicate_is_idempotent(client: TestClient) -> None:
    client.post("/api/settings/stopwords", json={"word": "yet"})
    r = client.post("/api/settings/stopwords", json={"word": "YET"})
    assert r.json()["total"] == 1


def test_remove_stopword(client: TestClient) -> None:
    client.post("/api/settings/stopwords", json={"word": "a"})
    client.post("/api/settings/stopwords", json={"word": "b"})

    r = client.delete("/api/settings/stopwords/a")
    assert r.status_code == 200
    assert r.json()["words"] == ["b"]


def test_add_stopword_validates_empty(client: TestClient) -> None:
    r = client.post("/api/settings/stopwords", json={"word": ""})
    assert r.status_code == 422


def test_generic_settings_still_work(client: TestClient) -> None:
    r = client.put("/api/settings/theme", json={"value": '"dark"'})
    assert r.status_code == 200

    r = client.get("/api/settings/theme")
    assert r.json()["value"] == '"dark"'


def test_stopwords_route_not_shadowed(client: TestClient) -> None:
    """The `/stopwords` route must not be captured by `/{key}`."""
    r = client.get("/api/settings/stopwords")
    assert r.status_code == 200
    assert "words" in r.json()