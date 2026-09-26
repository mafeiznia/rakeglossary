"""Meta endpoints: health check and app metadata."""

from __future__ import annotations

import sys

from fastapi import APIRouter
from pydantic import BaseModel

from app.core import version as v

router = APIRouter(prefix="/api", tags=["meta"])


class AuthorInfo(BaseModel):
    name_fa: str
    name_en: str
    role_fa: str
    role_en: str
    email: str
    linkedin: str
    website: str


class TechStack(BaseModel):
    frontend: str
    backend: str
    python: str
    database: str
    nlp: str


class AboutResponse(BaseModel):
    app_name: str
    version: str
    tagline_fa: str
    tagline_en: str
    license: str
    copyright_year: int
    author: AuthorInfo
    tech_stack: TechStack
    github: str
    desktop_mode: bool


@router.get(
    "/health",
    summary="Health check",
)
def health() -> dict:
    """Return a simple health check payload."""
    return {"status": "ok", "version": v.__version__, "name": v.APP_NAME}


@router.get(
    "/about",
    response_model=AboutResponse,
    summary="Application metadata (version, author, tech stack)",
)
def about() -> AboutResponse:
    """Return app identity and version information for the UI."""
    return AboutResponse(
        app_name=v.APP_NAME,
        version=v.__version__,
        tagline_fa=v.APP_TAGLINE_FA,
        tagline_en=v.APP_TAGLINE_EN,
        license=v.LICENSE,
        copyright_year=v.COPYRIGHT_YEAR,
        author=AuthorInfo(
            name_fa=v.AUTHOR_NAME_FA,
            name_en=v.AUTHOR_NAME_EN,
            role_fa=v.AUTHOR_ROLE_FA,
            role_en=v.AUTHOR_ROLE_EN,
            email=v.AUTHOR_EMAIL,
            linkedin=v.AUTHOR_LINKEDIN,
            website=v.AUTHOR_WEBSITE,
        ),
        tech_stack=TechStack(
            frontend="React 18 + Vite + Tailwind",
            backend="FastAPI + Uvicorn",
            python=v.python_version(),
            database="SQLite",
            nlp="spaCy + RAKE + YAKE",
        ),
        github=v.GITHUB_REPO,
        desktop_mode=bool(getattr(sys, "frozen", False)),
    )
