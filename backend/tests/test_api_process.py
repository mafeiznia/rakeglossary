"""Tests for the process + SSE endpoints."""
from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

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


def _mk_project_with_text(client: TestClient) -> str:
    r = client.post("/api/projects", json={"title": "T"})
    pid = r.json()["id"]
    client.post(
        f"/api/projects/{pid}/sources/text",
        json={"name": "ch1", "text": "Photosynthesis is a biological process."},
    )
    return pid


def test_start_process_mocked(client: TestClient) -> None:
    pid = _mk_project_with_text(client)
    with patch("app.api.process.pipeline_runner.start_pipeline") as mock_start:
        mock_start.return_value = None
        r = client.post(
            f"/api/process/{pid}",
            json={"num_terms": 5, "translate_terms": False},
        )
        assert r.status_code == 200
        mock_start.assert_called_once_with(pid)


def test_start_process_missing_project(client: TestClient) -> None:
    r = client.post("/api/process/no-such-id", json={})
    assert r.status_code == 404


def test_cancel_when_not_processing(client: TestClient) -> None:
    pid = _mk_project_with_text(client)
    r = client.post(f"/api/process/{pid}/cancel")
    assert r.status_code == 409