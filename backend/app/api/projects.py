"""Project endpoints: create (empty), list, read, update, delete."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api._helpers import project_to_read
from app.api.deps import ProjectDep, SessionDep
from app.schemas.project import (
    BookMetadataUpdate,
    ProjectCreateEmpty,
    ProjectListResponse,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from app.services import project_service
from app.services.storage import delete_project_dir

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an empty project (add sources separately)",
)
def create_project(
    payload: ProjectCreateEmpty,
    session: SessionDep,
) -> ProjectRead:
    project = project_service.create_empty(session, payload)
    return project_to_read(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects (paginated, newest first)",
)
def list_projects(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> ProjectListResponse:
    rows, total = project_service.list_paginated(session, page=page, page_size=page_size)
    return ProjectListResponse(
        items=[ProjectSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get a single project (with inline sources)",
)
def get_project(project: ProjectDep) -> ProjectRead:
    return project_to_read(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update project title or pipeline options",
)
def update_project(
    project: ProjectDep,
    payload: ProjectUpdate,
    session: SessionDep,
) -> ProjectRead:
    project = project_service.update_project(session, project, payload)
    return project_to_read(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project, its sources, and all glossary entries",
)
def delete_project(project: ProjectDep, session: SessionDep) -> None:
    pid = project.id
    # Delete the entire per-project uploads directory first
    delete_project_dir(pid)
    # DB cascade deletes sources + glossary entries
    project_service.delete(session, project)


# ---------------------------------------------------------------------------
# Book metadata
# ---------------------------------------------------------------------------


@router.put(
    "/{project_id}/metadata",
    response_model=ProjectRead,
    summary="Set or update the book metadata for a project",
)
def set_project_metadata(
    project: ProjectDep,
    payload: BookMetadataUpdate,
    session: SessionDep,
) -> ProjectRead:
    """Store the metadata as a JSON blob.

    The body accepts the full BookSpecsTemplate.json structure, or any
    subset of it. We store the blob as-is; interpretation happens at
    pipeline time.
    """
    metadata = payload.model_dump(exclude_none=True)
    project_service.set_book_metadata(session, project, metadata)
    return project_to_read(project)


@router.delete(
    "/{project_id}/metadata",
    response_model=ProjectRead,
    summary="Clear the book metadata for a project",
)
def clear_project_metadata(
    project: ProjectDep,
    session: SessionDep,
) -> ProjectRead:
    project_service.clear_book_metadata(session, project)
    return project_to_read(project)
