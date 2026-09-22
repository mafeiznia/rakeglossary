"""Project source endpoints: upload files, add text, list, update, delete."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.api.deps import ProjectDep, SessionDep
from app.core.logging import get_logger
from app.schemas.source import (
    ProjectSourceRead,
    ProjectSourceUpdate,
    TextSourceCreate,
)
from app.services import source_service
from app.services.storage import StorageError

log = get_logger("api.sources")

router = APIRouter(prefix="/api/projects/{project_id}/sources", tags=["sources"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[ProjectSourceRead],
    summary="List all sources of a project",
)
def list_sources(project: ProjectDep, session: SessionDep) -> list[ProjectSourceRead]:
    rows = source_service.list_for_project(session, project.id)
    return [ProjectSourceRead.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Upload files (multi-file)
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=list[ProjectSourceRead],
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more files as sources",
)
async def upload_sources(
    project: ProjectDep,
    session: SessionDep,
    files: Annotated[list[UploadFile], File(description="One or more PDF/DOCX/EPUB/TXT")],
) -> list[ProjectSourceRead]:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided.",
        )

    created: list = []
    errors: list[str] = []

    sorted_files = sorted(files, key=lambda f: (f.filename or "").lower())

    for f in sorted_files:
        original_name = f.filename or "upload"
        try:
            data = await f.read()
            src = source_service.add_file_source(session, project, data, original_name)
            created.append(src)
        except source_service.DuplicateSourceError as exc:
            log.info(f"Duplicate upload rejected '{original_name}': {exc}")
            errors.append(f"{original_name}: {exc}")
        except StorageError as exc:
            log.warning(f"Rejected upload '{original_name}': {exc}")
            errors.append(f"{original_name}: {exc}")
        except Exception as exc:
            log.exception(f"Failed to add file source '{original_name}'")
            errors.append(f"{original_name}: {exc}")
        finally:
            await f.close()

    if not created and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors),
        )

    session.refresh(project)
    return [ProjectSourceRead.model_validate(s) for s in created]


# ---------------------------------------------------------------------------
# Add text source
# ---------------------------------------------------------------------------


@router.post(
    "/text",
    response_model=ProjectSourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a raw text snippet as a source",
)
def add_text_source(
    project: ProjectDep,
    payload: TextSourceCreate,
    session: SessionDep,
) -> ProjectSourceRead:
    src = source_service.add_text_source(session, project, payload)
    return ProjectSourceRead.model_validate(src)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.patch(
    "/{source_id}",
    response_model=ProjectSourceRead,
    summary="Update a source (rename or toggle inclusion)",
)
def update_source(
    project: ProjectDep,
    source_id: int,
    payload: ProjectSourceUpdate,
    session: SessionDep,
) -> ProjectSourceRead:
    src = source_service.get(session, source_id)
    if src is None or src.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source #{source_id} not found in this project.",
        )
    updated = source_service.update_source(session, src, payload)
    return ProjectSourceRead.model_validate(updated)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a source (removes its file from disk too)",
)
def delete_source(
    project: ProjectDep,
    source_id: int,
    session: SessionDep,
) -> None:
    src = source_service.get(session, source_id)
    if src is None or src.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source #{source_id} not found in this project.",
        )
    source_service.delete_source(session, src)
