"""Tests for LLM config service and endpoints."""
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
from app.services import llm_config_service


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


# ---------------------------------------------------------------------------
# llm_config_service
# ---------------------------------------------------------------------------


def test_config_defaults(session: Session) -> None:
    cfg = llm_config_service.get_config(session)
    assert cfg.enabled is False
    assert cfg.provider == "openai"
    assert cfg.api_key == ""
    assert cfg.model == "gpt-4o-mini"


def test_config_roundtrip(session: Session) -> None:
    cfg = llm_config_service.LlmConfig(
        enabled=True,
        provider="openrouter",
        api_key="sk-test",
        model="openai/gpt-4o-mini",
    )
    llm_config_service.set_config(session, cfg)

    loaded = llm_config_service.get_config(session)
    assert loaded.enabled is True
    assert loaded.provider == "openrouter"
    assert loaded.api_key == "sk-test"


def test_config_clear(session: Session) -> None:
    llm_config_service.set_config(
        session,
        llm_config_service.LlmConfig(enabled=True, api_key="x"),
    )
    llm_config_service.clear_config(session)

    cfg = llm_config_service.get_config(session)
    assert cfg.enabled is False


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


def test_get_llm_providers(client: TestClient) -> None:
    r = client.get("/api/settings/llm/providers")
    assert r.status_code == 200
    body = r.json()
    keys = {p["key"] for p in body}
    # Core providers must be present
    assert {"openai", "openrouter", "gemini", "gapgpt", "custom"} <= keys
    # Extended providers
    assert "deepseek" in keys
    assert "groq" in keys


def test_get_llm_config_defaults(client: TestClient) -> None:
    r = client.get("/api/settings/llm")
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is False
    assert body["provider"] == "openai"
    assert body["has_api_key"] is False
    assert body["api_key_masked"] is None


def test_update_llm_config(client: TestClient) -> None:
    r = client.put(
        "/api/settings/llm",
        json={
            "enabled": True,
            "provider": "gapgpt",
            "api_key": "sk-1234567890abcdef",
            "model": "gpt-4o-mini",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is True
    assert body["provider"] == "gapgpt"
    assert body["has_api_key"] is True
    assert body["api_key_masked"] == "sk-1...cdef"


def test_update_llm_config_partial(client: TestClient) -> None:
    # First update with full config
    client.put(
        "/api/settings/llm",
        json={"enabled": True, "provider": "openai", "api_key": "sk-a"},
    )
    # Now partial update of just the model
    r = client.put("/api/settings/llm", json={"model": "gpt-4o"})
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "gpt-4o"
    # api_key should be preserved
    assert body["has_api_key"] is True


def test_clear_llm_config(client: TestClient) -> None:
    client.put("/api/settings/llm", json={"enabled": True, "api_key": "x"})
    r = client.delete("/api/settings/llm")
    assert r.status_code == 204

    r = client.get("/api/settings/llm")
    assert r.json()["enabled"] is False


def test_test_endpoint_when_disabled(client: TestClient) -> None:
    r = client.post("/api/settings/llm/test")
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_update_rejects_invalid_provider(client: TestClient) -> None:
    r = client.put("/api/settings/llm", json={"provider": "invalid"})
    assert r.status_code == 422