"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import export, glossary, meta, process, projects, sources
from app.api import settings as settings_api
from app.core.db import init_db
from app.core.logging import get_logger
from app.core.version import APP_NAME, __version__

log = get_logger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info(f"Starting {APP_NAME} v{__version__}")
    init_db()
    log.info("Database initialized.")
    yield
    log.info(f"Shutting down {APP_NAME}")


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{APP_NAME} API",
        version=__version__,
        description="Automated glossary generator (EN → FA)",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8765",
            "http://127.0.0.1:8765",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta.router)
    app.include_router(projects.router)
    app.include_router(sources.router)
    app.include_router(glossary.router)
    app.include_router(process.router)
    app.include_router(export.router)
    app.include_router(settings_api.router)

    return app


app = create_app()
