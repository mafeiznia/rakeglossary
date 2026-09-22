"""FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import export, glossary, meta, process, projects, sources
from app.api import settings as settings_api
from app.core.db import init_db
from app.core.logging import get_logger
from app.core.version import APP_NAME, __version__

log = get_logger("main")

# Frontend build directory (present only after `npm run build`)
def _frontend_dist() -> Path:
    """Return the directory containing the built SPA.

    - In a PyInstaller bundle: ``<_MEIPASS>/frontend/dist``
    - In dev:                  ``<root>/frontend/dist``
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend" / "dist"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


_FRONTEND_DIST = _frontend_dist()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info(f"Starting {APP_NAME} v{__version__}")
    init_db()
    log.info("Database initialized.")
    yield
    log.info(f"Shutting down {APP_NAME}")


def _mount_frontend_spa(app: FastAPI) -> None:
    """Serve `frontend/dist` as an SPA with index.html fallback.

    Registered AFTER all API routers so `/api/*` is never intercepted.
    """

    dist_resolved = _FRONTEND_DIST.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Never shadow the API
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve a real file (JS/CSS/assets/favicon/...)
        if full_path:
            candidate = (dist_resolved / full_path).resolve()
            try:
                candidate.relative_to(dist_resolved)  # path-traversal guard
            except ValueError:
                raise HTTPException(status_code=404, detail="Not found") from None
            if candidate.is_file():
                return FileResponse(candidate)

        # SPA fallback -> index.html
        index = dist_resolved / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend not built")
        return FileResponse(index)


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{APP_NAME} API",
        version=__version__,
        description="Automated glossary generator (EN -> FA)",
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

    # --- API routers (must come first) ---
    app.include_router(meta.router)
    app.include_router(projects.router)
    app.include_router(sources.router)
    app.include_router(glossary.router)
    app.include_router(process.router)
    app.include_router(export.router)
    app.include_router(settings_api.router)

    # --- Frontend SPA (production only) ---
    if _FRONTEND_DIST.is_dir():
        _mount_frontend_spa(app)
        log.info(f"Frontend SPA mounted from: {_FRONTEND_DIST}")
    else:
        log.info(
            f"Frontend dist not found at {_FRONTEND_DIST}; "
            "running in API-only mode (use Vite dev server on :5173)."
        )

    return app


app = create_app()
