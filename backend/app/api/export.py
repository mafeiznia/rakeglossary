"""Export endpoints: download glossary as CSV, XLSX, or TBX."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.deps import ProjectDep, SessionDep
from app.core.config import settings
from app.core.logging import get_logger
from app.services import desktop, export_service, glossary_service

log = get_logger("api.export")

router = APIRouter(prefix="/api", tags=["export"])

_ALLOWED_FORMATS = {"csv", "xlsx", "tbx"}
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\-]+")


def _safe_basename(title: str) -> str:
    stem = _SAFE_NAME_RE.sub("_", title.strip())[:60] or "glossary"
    return stem


class SaveExportResponse(BaseModel):
    path: str
    filename: str
    size_bytes: int
    folder_opened: bool


@router.get(
    "/export/{project_id}/{fmt}",
    summary="Download the glossary of a project in the given format",
)
def export_project(
    project: ProjectDep,
    fmt: str,
    session: SessionDep,
) -> FileResponse:
    fmt = fmt.lower()
    if fmt not in _ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{fmt}'. Use one of: {sorted(_ALLOWED_FORMATS)}",
        )

    entries = glossary_service.list_for_project(session, project.id)
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No glossary entries available for this project.",
        )

    basename = f"{_safe_basename(project.title)}_{project.id[:8]}"
    try:
        path = export_service.export(
            entries=entries,
            fmt=fmt,
            output_dir=settings.paths.exports,
            basename=basename,
        )
    except Exception as exc:
        log.exception(f"Export failed for project {project.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {exc}",
        ) from exc

    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/octet-stream",
    )


@router.post(
    "/export/{project_id}/{fmt}/save",
    response_model=SaveExportResponse,
    summary="Save the glossary to the user's Downloads folder and open it",
)
def save_export_to_downloads(
    project: ProjectDep,
    fmt: str,
    session: SessionDep,
) -> SaveExportResponse:
    """Save the glossary to the user's Downloads folder and reveal it.

    This is the endpoint used by the desktop (pywebview) build where
    browser-style downloads are not available.
    """
    fmt = fmt.lower()
    if fmt not in _ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{fmt}'. Use one of: {sorted(_ALLOWED_FORMATS)}",
        )

    entries = glossary_service.list_for_project(session, project.id)
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No glossary entries available for this project.",
        )

    basename = f"{_safe_basename(project.title)}_{project.id[:8]}"
    downloads = desktop.get_downloads_dir()

    try:
        path = export_service.export(
            entries=entries,
            fmt=fmt,
            output_dir=downloads,
            basename=basename,
        )
    except Exception as exc:
        log.exception(f"Export-save failed for project {project.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {exc}",
        ) from exc

    opened = desktop.open_in_file_manager(path, select=True)
    log.info(
        f"Saved export to Downloads: {path} "
        f"(folder_opened={opened}, size={path.stat().st_size} bytes)"
    )

    return SaveExportResponse(
        path=str(path),
        filename=path.name,
        size_bytes=path.stat().st_size,
        folder_opened=opened,
    )
