"""Tests for user LLM model history and fetched model cache."""
from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 — register ORM models
from app.core.db import get_session
from app.main import create_app
from app.services import llm_config_service

from app.core.db import Base

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


# ---------------------------------------------------------------------------
# User model history
# ---------------------------------------------------------------------------


def test_get_user_models_empty(session: Session) -> None:
    assert llm_config_service.get_user_models(session) == {}


def test_add_user_model_new_provider(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    result = llm_config_service.get_user_models(session)
    assert result == {"openai": ["gpt-4o"]}


def test_add_user_model_moves_to_front(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    llm_config_service.add_user_model(session, "openai", "gpt-4o-mini")
    result = llm_config_service.get_user_models(session)
    # Most recent first
    assert result["openai"] == ["gpt-4o-mini", "gpt-4o"]


def test_add_user_model_duplicate_moves_to_front(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    llm_config_service.add_user_model(session, "openai", "gpt-4o-mini")
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    result = llm_config_service.get_user_models(session)
    assert result["openai"] == ["gpt-4o", "gpt-4o-mini"]
    assert len(result["openai"]) == 2


def test_add_user_model_strips_whitespace(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "  gpt-4o  ")
    result = llm_config_service.get_user_models(session)
    assert result["openai"] == ["gpt-4o"]


def test_add_user_model_ignores_empty(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "")
    llm_config_service.add_user_model(session, "openai", "   ")
    assert llm_config_service.get_user_models(session) == {}


def test_remove_user_model(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    llm_config_service.add_user_model(session, "openai", "gpt-4o-mini")
    llm_config_service.remove_user_model(session, "openai", "gpt-4o")
    result = llm_config_service.get_user_models(session)
    assert result["openai"] == ["gpt-4o-mini"]


def test_remove_user_model_last_removes_provider(session: Session) -> None:
    llm_config_service.add_user_model(session, "openai", "gpt-4o")
    llm_config_service.remove_user_model(session, "openai", "gpt-4o")
    assert llm_config_service.get_user_models(session) == {}


# ---------------------------------------------------------------------------
# Fetched models cache (24-hour TTL)
# ---------------------------------------------------------------------------


def test_cache_set_and_get(session: Session) -> None:
    llm_config_service.set_models_cache(
        session, "openai", ["gpt-4o", "gpt-4o-mini"]
    )
    cached = llm_config_service.get_models_cache(session, "openai")
    assert cached == ["gpt-4o", "gpt-4o-mini"]


def test_cache_get_missing(session: Session) -> None:
    assert llm_config_service.get_models_cache(session, "openai") is None


def test_cache_fresh_within_ttl(session: Session) -> None:
    llm_config_service.set_models_cache(session, "openai", ["gpt-4o"])
    cached = llm_config_service.get_models_cache(session, "openai")
    assert cached == ["gpt-4o"]


def test_cache_expires_after_ttl(session: Session, monkeypatch) -> None:
    llm_config_service.set_models_cache(session, "openai", ["gpt-4o"])

    # Simulate 25 hours passing
    real_now = datetime.now(UTC)

    def fake_utcnow() -> datetime:
        return real_now + timedelta(hours=25)

    monkeypatch.setattr(llm_config_service, "_utcnow", fake_utcnow)
    assert llm_config_service.get_models_cache(session, "openai") is None


def test_clear_cache(session: Session) -> None:
    llm_config_service.set_models_cache(session, "openai", ["gpt-4o"])
    llm_config_service.clear_models_cache(session, "openai")
    assert llm_config_service.get_models_cache(session, "openai") is None
    
    

# ---------------------------------------------------------------------------
# Union logic: list_available_models
# ---------------------------------------------------------------------------


def test_list_available_models_unknown_provider(session: Session) -> None:
    """Unknown provider with no history returns empty list."""
    result = llm_config_service.list_available_models(session, "unknown-provider")
    assert result == []


def test_list_available_models_only_suggested(session: Session) -> None:
    """OpenAI has suggested models in the JSON; with no user data, those show."""
    result = llm_config_service.list_available_models(session, "openai")
    # Should contain at least the default model
    assert "gpt-4o-mini" in result
    # Non-empty
    assert len(result) > 0


def test_list_available_models_user_first(session: Session) -> None:
    """User history has priority in ordering."""
    llm_config_service.add_user_model(session, "openai", "my-custom-model")
    result = llm_config_service.list_available_models(session, "openai")
    # User models come first
    assert result[0] == "my-custom-model"
    # Suggested models are still present after
    assert "gpt-4o-mini" in result


def test_list_available_models_deduplicates(session: Session) -> None:
    """A model present in both user history and suggested appears once."""
    llm_config_service.add_user_model(session, "openai", "gpt-4o-mini")
    result = llm_config_service.list_available_models(session, "openai")
    assert result.count("gpt-4o-mini") == 1
    # And it's first (user priority)
    assert result[0] == "gpt-4o-mini"


def test_list_available_models_includes_cached(session: Session) -> None:
    """Cached models from a provider fetch appear in the union."""
    llm_config_service.set_models_cache(
        session, "openai", ["fetched-model-a", "fetched-model-b"]
    )
    result = llm_config_service.list_available_models(session, "openai")
    assert "fetched-model-a" in result
    assert "fetched-model-b" in result


def test_list_available_models_priority_order(session: Session) -> None:
    """Order must be: user, cached, suggested."""
    llm_config_service.add_user_model(session, "openai", "user-model")
    llm_config_service.set_models_cache(session, "openai", ["cached-model"])
    result = llm_config_service.list_available_models(session, "openai")
    # user first
    assert result[0] == "user-model"
    # cached next
    assert result[1] == "cached-model"
    # suggested after
    assert "gpt-4o-mini" in result[2:]


def test_list_available_models_expired_cache_not_shown(
    session: Session, monkeypatch
) -> None:
    """Expired cache must not appear in the union."""
    from datetime import UTC, datetime, timedelta

    llm_config_service.set_models_cache(session, "openai", ["old-model"])
    # Jump 25 hours forward
    real_now = datetime.now(UTC)
    monkeypatch.setattr(
        llm_config_service,
        "_utcnow",
        lambda: real_now + timedelta(hours=25),
    )
    result = llm_config_service.list_available_models(session, "openai")
    assert "old-model" not in result
    


# ---------------------------------------------------------------------------
# fetch_provider_models (Phase 3)
# ---------------------------------------------------------------------------


def _mock_models_response(model_ids: list[str]) -> MagicMock:
    """Build a fake OpenAI /v1/models response."""
    resp = MagicMock()
    items = []
    for mid in model_ids:
        item = MagicMock()
        item.id = mid
        items.append(item)
    resp.data = items
    return resp


def test_fetch_provider_models_returns_ids() -> None:
    from app.pipeline.llm_client import fetch_provider_models

    mock_client = MagicMock()
    mock_client.models.list.return_value = _mock_models_response(
        ["gpt-4o", "gpt-4o-mini", "o1-preview"]
    )

    with patch("openai.OpenAI", return_value=mock_client):
        result = fetch_provider_models(
            api_key="sk-test", base_url=None, provider="openai"
        )

    assert result == ["gpt-4o", "gpt-4o-mini", "o1-preview"]


def test_fetch_provider_models_sorted() -> None:
    from app.pipeline.llm_client import fetch_provider_models

    mock_client = MagicMock()
    mock_client.models.list.return_value = _mock_models_response(
        ["z-model", "a-model", "m-model"]
    )

    with patch("openai.OpenAI", return_value=mock_client):
        result = fetch_provider_models(
            api_key="sk-test", base_url=None, provider="openai"
        )

    assert result == ["a-model", "m-model", "z-model"]


def test_fetch_provider_models_empty_response() -> None:
    from app.pipeline.llm_client import fetch_provider_models

    mock_client = MagicMock()
    mock_client.models.list.return_value = _mock_models_response([])

    with patch("openai.OpenAI", return_value=mock_client):
        result = fetch_provider_models(
            api_key="sk-test", base_url=None, provider="openai"
        )

    assert result == []


def test_fetch_provider_models_filters_empty_ids() -> None:
    from app.pipeline.llm_client import fetch_provider_models

    mock_client = MagicMock()
    # Mix of valid and empty ids
    resp = MagicMock()
    items = []
    for mid in ["gpt-4o", "", "  ", "gpt-4o-mini"]:
        item = MagicMock()
        item.id = mid
        items.append(item)
    resp.data = items
    mock_client.models.list.return_value = resp

    with patch("openai.OpenAI", return_value=mock_client):
        result = fetch_provider_models(
            api_key="sk-test", base_url=None, provider="openai"
        )

    assert result == ["gpt-4o", "gpt-4o-mini"]


def test_fetch_provider_models_raises_on_api_error() -> None:
    import pytest as pytest_module

    from app.pipeline.llm_client import (
        ModelFetchError,
        fetch_provider_models,
    )

    mock_client = MagicMock()
    mock_client.models.list.side_effect = RuntimeError("network down")

    with patch("openai.OpenAI", return_value=mock_client):
        with pytest_module.raises(ModelFetchError):
            fetch_provider_models(
                api_key="sk-test", base_url=None, provider="openai"
            )


def test_fetch_provider_models_passes_base_url() -> None:
    from app.pipeline.llm_client import fetch_provider_models

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.models.list.return_value = _mock_models_response(["x"])
        mock_openai.return_value = mock_client

        fetch_provider_models(
            api_key="sk-test",
            base_url="https://custom.example.com/v1",
            provider="custom",
        )

        # OpenAI must be constructed with our base_url
        call_kwargs = mock_openai.call_args.kwargs
        assert call_kwargs.get("base_url") == "https://custom.example.com/v1"
        


# ---------------------------------------------------------------------------
# API endpoint tests (Phase 4)
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    """TestClient with an isolated in-memory DB."""
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
    with TestClient(app) as c:
        yield c


def _configure_openai(api_client: TestClient) -> None:
    """Enable LLM with OpenAI provider via the API."""
    r = api_client.put(
        "/api/settings/llm",
        json={
            "enabled": True,
            "provider": "openai",
            "api_key": "sk-test",
            "model": "gpt-4o-mini",
        },
    )
    assert r.status_code == 200


def test_list_models_unknown_provider(api_client: TestClient) -> None:
    r = api_client.get("/api/settings/llm/models?provider=unknown-xyz")
    assert r.status_code == 200
    assert r.json()["models"] == []


def test_list_models_includes_suggested(api_client: TestClient) -> None:
    r = api_client.get("/api/settings/llm/models?provider=openai")
    assert r.status_code == 200
    models_list = r.json()["models"]
    assert "gpt-4o-mini" in models_list


def test_list_models_user_history_first(api_client: TestClient) -> None:
    _configure_openai(api_client)
    # Save a custom model → should be added to history
    r = api_client.put(
        "/api/settings/llm",
        json={"model": "my-custom-model"},
    )
    assert r.status_code == 200

    r = api_client.get("/api/settings/llm/models?provider=openai")
    assert r.status_code == 200
    models_list = r.json()["models"]
    assert models_list[0] == "my-custom-model"


def test_refresh_models_fetches_and_caches(api_client: TestClient) -> None:
    _configure_openai(api_client)

    from unittest.mock import patch

    with patch(
        "app.pipeline.llm_client.fetch_provider_models",
        return_value=["fetched-a", "fetched-b"],
    ):
        r = api_client.post("/api/settings/llm/models/refresh?provider=openai")

    assert r.status_code == 200
    returned = r.json()["models"]
    # Endpoint returns the union; fetched items must be present and
    # must come before the suggested models.
    assert "fetched-a" in returned
    assert "fetched-b" in returned
    # Suggested models appear after fetched ones
    assert returned.index("fetched-a") < returned.index("gpt-4o-mini")

    # Now /models should also include them
    r = api_client.get("/api/settings/llm/models?provider=openai")
    assert "fetched-a" in r.json()["models"]


def test_refresh_models_requires_configured_llm(api_client: TestClient) -> None:
    # Without any config, refresh must fail
    r = api_client.post("/api/settings/llm/models/refresh?provider=openai")
    assert r.status_code == 400


def test_refresh_models_handles_fetch_error(api_client: TestClient) -> None:
    _configure_openai(api_client)

    from unittest.mock import patch

    from app.pipeline.llm_client import ModelFetchError

    with patch(
        "app.pipeline.llm_client.fetch_provider_models",
        side_effect=ModelFetchError("boom"),
    ):
        r = api_client.post("/api/settings/llm/models/refresh?provider=openai")

    assert r.status_code == 502
    assert "boom" in r.json()["detail"]


def test_delete_user_model(api_client: TestClient) -> None:
    _configure_openai(api_client)
    # Add two models
    api_client.put("/api/settings/llm", json={"model": "model-a"})
    api_client.put("/api/settings/llm", json={"model": "model-b"})

    # Delete one
    r = api_client.delete("/api/settings/llm/models/user/openai/model-a")
    assert r.status_code == 204

    # Check history via /models
    r = api_client.get("/api/settings/llm/models?provider=openai")
    models_list = r.json()["models"]
    assert "model-a" not in models_list[:2]  # not in user history position
    assert "model-b" in models_list


def test_delete_user_model_not_found_is_idempotent(
    api_client: TestClient,
) -> None:
    """Deleting a non-existent model must not error."""
    r = api_client.delete("/api/settings/llm/models/user/openai/nope")
    assert r.status_code == 204        