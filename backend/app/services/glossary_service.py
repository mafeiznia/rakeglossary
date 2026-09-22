"""CRUD operations for GlossaryEntry entities."""

from __future__ import annotations

import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.glossary_entry import GlossaryEntry
from app.pipeline.glossary import GlossaryEntry as PipelineEntry
from app.schemas.glossary import GlossaryEntryUpdate

log = get_logger("services.glossary")


def _serialize_alternatives(alternatives: list[str] | None) -> str | None:
    """Convert a list of alternatives to a JSON string for storage."""
    if not alternatives:
        return None
    return json.dumps(alternatives, ensure_ascii=False)


def replace_entries(
    session: Session,
    project_id: str,
    entries: list[PipelineEntry],
) -> list[GlossaryEntry]:
    """Delete existing entries for `project_id` and insert new ones."""
    session.execute(delete(GlossaryEntry).where(GlossaryEntry.project_id == project_id))

    rows: list[GlossaryEntry] = []
    for e in entries:
        rows.append(
            GlossaryEntry(
                project_id=project_id,
                english_term=e.english_term,
                persian_term=e.persian_term,
                english_definition=e.english_definition,
                persian_definition=e.persian_definition,
                source=e.source,
                score=e.score,
                frequency=e.frequency,
                context=e.context,
                is_edited=False,
                # --- AI Mode extras ---
                pos=e.pos,
                category=e.category,
                persian_alternatives=_serialize_alternatives(e.persian_alternatives),
                translator_note=e.translator_note,
                persian_transliteration=e.persian_transliteration,
            )
        )
    session.add_all(rows)
    session.commit()
    log.info(
        f"Saved {len(rows)} glossary entries for project {project_id[:8]} "
        f"(with AI extras: "
        f"{sum(1 for r in rows if r.pos)}, "
        f"{sum(1 for r in rows if r.translator_note)})"
    )
    return rows


def list_for_project(
    session: Session,
    project_id: str,
) -> list[GlossaryEntry]:
    """Return all entries for a project, ordered by score DESC."""
    return list(
        session.execute(
            select(GlossaryEntry)
            .where(GlossaryEntry.project_id == project_id)
            .order_by(GlossaryEntry.score.desc(), GlossaryEntry.id.asc())
        )
        .scalars()
        .all()
    )


def get(session: Session, entry_id: int) -> GlossaryEntry | None:
    return session.get(GlossaryEntry, entry_id)


def update(
    session: Session,
    entry: GlossaryEntry,
    payload: GlossaryEntryUpdate,
) -> GlossaryEntry:
    """Apply manual edits to a glossary entry."""
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(entry, field, value)

    if "is_edited" not in data:
        entry.is_edited = True

    session.commit()
    session.refresh(entry)
    log.info(f"Updated glossary entry #{entry.id} (edited={entry.is_edited})")
    return entry


def delete_entry(session: Session, entry: GlossaryEntry) -> None:
    eid = entry.id
    session.delete(entry)
    session.commit()
    log.info(f"Deleted glossary entry #{eid}")
