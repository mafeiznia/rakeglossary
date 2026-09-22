"""Tests for /api/health and /api/about endpoints."""
from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient

from app.core import version as v
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- /api/health ---

def test_health_returns_ok(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == v.__version__
    assert body["name"] == v.APP_NAME


# --- /api/about ---

def test_about_returns_all_top_level_fields(client: TestClient) -> None:
    r = client.get("/api/about")
    assert r.status_code == 200
    body = r.json()

    # Top-level keys
    for key in (
        "app_name",
        "version",
        "tagline_fa",
        "tagline_en",
        "license",
        "copyright_year",
        "author",
        "tech_stack",
        "github",
    ):
        assert key in body, f"missing key: {key}"


def test_about_matches_version_module(client: TestClient) -> None:
    body = client.get("/api/about").json()
    assert body["app_name"] == v.APP_NAME
    assert body["version"] == v.__version__
    assert body["license"] == v.LICENSE
    assert body["copyright_year"] == v.COPYRIGHT_YEAR
    assert body["github"] == v.GITHUB_REPO


def test_about_author_block(client: TestClient) -> None:
    body = client.get("/api/about").json()
    author = body["author"]

    assert author["name_fa"] == v.AUTHOR_NAME_FA
    assert author["name_en"] == v.AUTHOR_NAME_EN
    assert author["role_fa"] == v.AUTHOR_ROLE_FA
    assert author["role_en"] == v.AUTHOR_ROLE_EN
    assert author["email"] == v.AUTHOR_EMAIL
    assert author["linkedin"] == v.AUTHOR_LINKEDIN
    assert author["website"] == v.AUTHOR_WEBSITE


def test_about_tech_stack_block(client: TestClient) -> None:
    body = client.get("/api/about").json()
    tech = body["tech_stack"]

    assert tech["frontend"] == "React 18 + Vite + Tailwind"
    assert tech["backend"] == "FastAPI + Uvicorn"
    assert tech["database"] == "SQLite"
    assert tech["nlp"] == "spaCy + RAKE + YAKE"

    # Python version comes from the runtime — verify format MAJOR.MINOR.PATCH
    parts = tech["python"].split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)

    # And it must match the current interpreter
    expected = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert tech["python"] == expected


def test_about_taglines_present(client: TestClient) -> None:
    body = client.get("/api/about").json()
    assert body["tagline_fa"]  # non-empty
    assert body["tagline_en"]  # non-empty
    assert body["tagline_fa"] != body["tagline_en"]