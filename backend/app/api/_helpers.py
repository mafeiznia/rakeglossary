"""Shared helpers for API routers."""

from __future__ import annotations

import json

from app.schemas.project import ProjectRead
from app.schemas.source import ProjectSourceRead


def project_to_read(project) -> ProjectRead:
    """Convert ORM Project to ProjectRead, parsing book_metadata.

    Handles:
    - `book_metadata` stored as a JSON string → parsed to dict
    - `processing_mode` stored as Enum → converted to string
    - `sources` relationship → serialized list
    """
    parsed_metadata = None
    if project.book_metadata:
        try:
            parsed_metadata = json.loads(project.book_metadata)
        except (json.JSONDecodeError, TypeError):
            parsed_metadata = None

    pm = project.processing_mode
    if hasattr(pm, "value"):
        pm = pm.value

    return ProjectRead(
        id=project.id,
        title=project.title,
        status=project.status,
        word_count=project.word_count,
        source_count=project.source_count,
        num_terms=project.num_terms,
        created_at=project.created_at,
        updated_at=project.updated_at,
        finished_at=project.finished_at,
        translate_terms=project.translate_terms,
        translate_definitions=project.translate_definitions,
        terms_per_1k_words=project.terms_per_1k_words,
        translation_provider=project.translation_provider,
        processing_mode=pm,
        use_spacy=project.use_spacy,
        use_rake=project.use_rake,
        use_yake=project.use_yake,
        use_ner=project.use_ner,
        error_message=project.error_message,
        started_at=project.started_at,
        sources=[ProjectSourceRead.model_validate(s) for s in project.sources],
        book_metadata=parsed_metadata,
    )
