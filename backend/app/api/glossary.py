"""Glossary endpoints: list, update, delete entries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ProjectDep, SessionDep
from app.schemas.glossary import (
    GlossaryEntryRead,
    GlossaryEntryUpdate,
    GlossaryResponse,
)
from app.services import glossary_service

router = APIRouter(prefix="/api", tags=["glossary"])


@router.get(
    "/projects/{project_id}/glossary",
    response_model=GlossaryResponse,
    summary="Get all glossary entries for a project",
)
def get_glossary(project: ProjectDep, session: SessionDep) -> GlossaryResponse:
    entries = glossary_service.list_for_project(session, project.id)
    return GlossaryResponse(
        project_id=project.id,
        entries=[GlossaryEntryRead.model_validate(e) for e in entries],
        total=len(entries),
    )


@router.patch(
    "/glossary/{entry_id}",
    response_model=GlossaryEntryRead,
    summary="Update a single glossary entry (manual edit)",
)
def update_entry(
    entry_id: int,
    payload: GlossaryEntryUpdate,
    session: SessionDep,
) -> GlossaryEntryRead:
    entry = glossary_service.get(session, entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glossary entry #{entry_id} not found.",
        )
    updated = glossary_service.update(session, entry, payload)
    return GlossaryEntryRead.model_validate(updated)


@router.delete(
    "/glossary/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single glossary entry",
)
def delete_entry(entry_id: int, session: SessionDep) -> None:
    entry = glossary_service.get(session, entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Glossary entry #{entry_id} not found.",
        )
    glossary_service.delete_entry(session, entry)
