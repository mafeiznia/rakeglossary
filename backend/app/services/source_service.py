"""CRUD operations for ProjectSource entities."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.project import Project
from app.models.project_source import ProjectSource, SourceType
from app.pipeline.extractors import load_text_from_source
from app.schemas.source import ProjectSourceUpdate, TextSourceCreate
from app.services.storage import (
    delete_upload,
    save_upload_for_project,
)

log = get_logger("services.source")


class DuplicateSourceError(Exception):
    """Raised when a source with the same content already exists."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resort_sources(session: Session, project_id: str) -> None:
    """Reassign order_index so sources are sorted alphabetically by name."""
    rows = list(
        session.execute(
            select(ProjectSource)
            .where(ProjectSource.project_id == project_id)
            .order_by(ProjectSource.original_name.asc(), ProjectSource.id.asc())
        )
        .scalars()
        .all()
    )
    for i, src in enumerate(rows):
        src.order_index = i
    session.commit()


def recompute_aggregates(session: Session, project: Project) -> None:
    """Refresh cached `word_count` and `source_count` on the project.

    `source_count` counts only *included* sources.
    """
    total_words = session.scalar(
        select(func.coalesce(func.sum(ProjectSource.word_count), 0)).where(
            ProjectSource.project_id == project.id,
            ProjectSource.included.is_(True),
        )
    )
    count = session.scalar(
        select(func.count())
        .select_from(ProjectSource)
        .where(
            ProjectSource.project_id == project.id,
            ProjectSource.included.is_(True),
        )
    )
    project.word_count = int(total_words or 0)
    project.source_count = int(count or 0)
    session.commit()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def add_file_source(
    session: Session,
    project: Project,
    file_bytes: bytes,
    original_name: str,
) -> ProjectSource:
    """Save the file to disk, extract its text, and register a source row.

    Raises:
        DuplicateSourceError: if an identical file (same content hash)
            is already attached to this project.
    """
    content_hash = _sha256(file_bytes)

    existing = session.scalar(
        select(ProjectSource).where(
            ProjectSource.project_id == project.id,
            ProjectSource.file_hash == content_hash,
        )
    )
    if existing is not None:
        raise DuplicateSourceError(
            f"Duplicate file content. Already attached as '{existing.original_name}'."
        )

    path = save_upload_for_project(file_bytes, original_name, project.id, project.title)

    text = load_text_from_source(file_path=str(path))
    word_count = len(text.split())

    source = ProjectSource(
        project_id=project.id,
        source_type=SourceType.FILE,
        path=str(path),
        text_content=None,
        original_name=Path(original_name).name,
        file_hash=content_hash,
        word_count=word_count,
        order_index=0,
        included=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    _resort_sources(session, project.id)
    recompute_aggregates(session, project)
    log.info(
        f"Added file source '{source.original_name}' "
        f"({word_count} words) to project {project.id[:8]}"
    )
    return source


def add_text_source(
    session: Session,
    project: Project,
    payload: TextSourceCreate,
) -> ProjectSource:
    """Register a raw text snippet as a source."""
    text = payload.text.strip()
    word_count = len(text.split())

    source = ProjectSource(
        project_id=project.id,
        source_type=SourceType.TEXT,
        path=None,
        text_content=text,
        original_name=payload.name.strip(),
        file_hash=None,
        word_count=word_count,
        order_index=0,
        included=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    _resort_sources(session, project.id)
    recompute_aggregates(session, project)
    log.info(
        f"Added text source '{source.original_name}' "
        f"({word_count} words) to project {project.id[:8]}"
    )
    return source


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def list_for_project(session: Session, project_id: str) -> list[ProjectSource]:
    return list(
        session.execute(
            select(ProjectSource)
            .where(ProjectSource.project_id == project_id)
            .order_by(ProjectSource.order_index.asc(), ProjectSource.id.asc())
        )
        .scalars()
        .all()
    )


def get(session: Session, source_id: int) -> ProjectSource | None:
    return session.get(ProjectSource, source_id)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_source(
    session: Session,
    source: ProjectSource,
    payload: ProjectSourceUpdate,
) -> ProjectSource:
    data = payload.model_dump(exclude_unset=True)

    if "original_name" in data:
        source.original_name = data["original_name"]
    if "included" in data:
        source.included = data["included"]

    session.commit()
    session.refresh(source)

    # re-sort if name changed
    if "original_name" in data:
        _resort_sources(session, source.project_id)

    project = session.get(Project, source.project_id)
    if project is not None:
        recompute_aggregates(session, project)

    return source


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete_source(session: Session, source: ProjectSource) -> None:
    project_id = source.project_id
    path = source.path
    sid = source.id

    session.delete(source)
    session.commit()

    if path:
        delete_upload(path)

    project = session.get(Project, project_id)
    if project is not None:
        recompute_aggregates(session, project)

    log.info(f"Deleted source #{sid} from project {project_id[:8]}")


def delete_all_for_project(session: Session, project_id: str) -> None:
    session.execute(delete(ProjectSource).where(ProjectSource.project_id == project_id))
    session.commit()
