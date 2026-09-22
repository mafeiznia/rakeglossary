"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.models.project import Project
from app.services import project_service

SessionDep = Annotated[Session, Depends(get_session)]


def get_project_or_404(
    project_id: str,
    session: SessionDep,
) -> Project:
    """Load a project by ID or raise 404."""
    project = project_service.get(session, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project


ProjectDep = Annotated[Project, Depends(get_project_or_404)]
