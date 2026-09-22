"""CRUD operations for Project entities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path  # <-- اضافه کن

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.project import ProcessingMode, Project, ProjectStatus
from app.models.project_source import ProjectSource
from app.schemas.project import ProcessRequest, ProjectCreateEmpty
from app.services.storage import (
    get_project_dir,
    rename_project_folder,
)

log = get_logger("services.project")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_empty(session: Session, payload: ProjectCreateEmpty) -> Project:
    """Create a project with no sources yet, plus its data folder."""
    project = Project(
        title=payload.title,
        status=ProjectStatus.PENDING,
        num_terms=payload.num_terms,
        terms_per_1k_words=payload.terms_per_1k_words,
        translate_terms=payload.translate_terms,
        translate_definitions=payload.translate_definitions,
        translation_provider=payload.translation_provider,
        processing_mode=ProcessingMode(payload.processing_mode),
        use_spacy=payload.use_spacy,
        use_rake=payload.use_rake,
        use_yake=payload.use_yake,
        use_ner=payload.use_ner,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    # Create the on-disk folder immediately
    get_project_dir(project.id, project.title)

    log.info(f"Created project {project.id[:8]} '{project.title}'")
    return project


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get(session: Session, project_id: str) -> Project | None:
    return session.get(Project, project_id)


def update_project(
    session: Session,
    project: Project,
    payload,  # ProjectUpdate
) -> Project:
    """Apply a partial update, and rename the folder if the title changed."""
    data = payload.model_dump(exclude_unset=True)
    old_title = project.title
    title_changed = "title" in data and data["title"] != old_title

    for field, value in data.items():
        setattr(project, field, value)
    session.commit()
    session.refresh(project)

    if title_changed:
        _rename_project_folder_and_paths(session, project, old_title)

    return project


def _rename_project_folder_and_paths(
    session: Session,
    project: Project,
    old_title: str,
) -> None:
    """Rename the project's folder and rewrite all source paths."""
    new_dir = rename_project_folder(project.id, old_title, project.title)
    if new_dir is None:
        return

    sources = list(
        session.execute(
            select(ProjectSource).where(ProjectSource.project_id == project.id)
        ).scalars()
    )
    for src in sources:
        if not src.path:
            continue
        old_path = Path(src.path)
        new_path = new_dir / old_path.name
        if new_path != old_path:
            src.path = str(new_path)
    session.commit()
    log.info(f"Updated {len(sources)} source path(s) after folder rename.")


def list_paginated(
    session: Session,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Project], int]:
    """Return (projects, total_count) ordered by newest first."""
    page = max(page, 1)
    page_size = max(min(page_size, 200), 1)

    total = session.scalar(select(func.count()).select_from(Project)) or 0
    rows = (
        session.execute(
            select(Project)
            .order_by(Project.created_at.desc(), Project.order_seq.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return list(rows), int(total)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def apply_process_options(
    session: Session,
    project: Project,
    options: ProcessRequest,
) -> Project:
    """Copy pipeline options onto the project row."""
    project.num_terms = options.num_terms
    project.terms_per_1k_words = options.terms_per_1k_words
    project.translate_terms = options.translate_terms
    project.translate_definitions = options.translate_definitions
    project.translation_provider = options.translation_provider
    project.processing_mode = ProcessingMode(options.processing_mode)
    project.use_spacy = options.use_spacy
    project.use_rake = options.use_rake
    project.use_yake = options.use_yake
    project.use_ner = options.use_ner
    session.commit()
    session.refresh(project)
    return project


def mark_processing(session: Session, project: Project) -> Project:
    project.status = ProjectStatus.PROCESSING
    project.error_message = None
    project.started_at = _utcnow()
    session.commit()
    session.refresh(project)
    return project


def mark_done(session: Session, project: Project) -> Project:
    project.status = ProjectStatus.DONE
    project.finished_at = _utcnow()
    session.commit()
    session.refresh(project)
    return project


def mark_failed(session: Session, project: Project, error: str) -> Project:
    project.status = ProjectStatus.FAILED
    project.error_message = error[:2000]
    project.finished_at = _utcnow()
    session.commit()
    session.refresh(project)
    return project


def mark_cancelled(session: Session, project: Project, reason: str = "") -> Project:
    project.status = ProjectStatus.CANCELLED
    project.error_message = reason[:2000] or "Cancelled by user."
    project.finished_at = _utcnow()
    session.commit()
    session.refresh(project)
    return project


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete(session: Session, project: Project) -> None:
    """Delete a project, cascading to sources and glossary entries.

    Note: physical file cleanup is the caller's responsibility
    (see `api.projects.delete_project`).
    """
    pid = project.id
    session.delete(project)
    session.commit()
    log.info(f"Deleted project {pid[:8]}")


# ---------------------------------------------------------------------------
# Book metadata
# ---------------------------------------------------------------------------


def set_book_metadata(
    session: Session,
    project: Project,
    metadata: dict,
) -> Project:
    """Store the book metadata as a JSON blob."""
    project.book_metadata = json.dumps(metadata, ensure_ascii=False)
    session.commit()
    session.refresh(project)
    log.info(f"Updated book metadata for project {project.id[:8]}")
    return project


def get_book_metadata(project: Project) -> dict | None:
    """Return the parsed metadata dict, or None."""
    if not project.book_metadata:
        return None
    try:
        return json.loads(project.book_metadata)
    except json.JSONDecodeError:
        log.warning(f"Project {project.id[:8]} has invalid metadata JSON; returning None.")
        return None


def clear_book_metadata(session: Session, project: Project) -> Project:
    project.book_metadata = None
    session.commit()
    session.refresh(project)
    log.info(f"Cleared book metadata for project {project.id[:8]}")
    return project
