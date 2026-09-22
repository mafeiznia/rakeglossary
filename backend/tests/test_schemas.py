"""Tests for Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.project import ProjectStatus
from app.models.project_source import SourceType
from app.schemas import (
    GlossaryEntryRead,
    GlossaryEntryUpdate,
    ProcessRequest,
    ProjectCreateEmpty,
    ProjectRead,
    ProjectSourceRead,
    ProjectSummary,
    SettingRead,
    SettingUpdate,
    TextSourceCreate,
)


# ---------------------------------------------------------------------------
# ProjectCreateEmpty
# ---------------------------------------------------------------------------


def test_create_empty_valid() -> None:
    s = ProjectCreateEmpty(title="Book")
    assert s.title == "Book"
    assert s.num_terms == 500
    assert s.terms_per_1k_words == 15.0
    assert s.translate_terms is True
    assert s.use_ner is True


def test_create_empty_strips_title() -> None:
    s = ProjectCreateEmpty(title="  Book  ")
    assert s.title == "Book"


def test_create_empty_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        ProjectCreateEmpty(title="   ")


def test_create_empty_num_terms_bounds() -> None:
    # num_terms: 1..2000
    with pytest.raises(ValidationError):
        ProjectCreateEmpty(title="T", num_terms=0)
    with pytest.raises(ValidationError):
        ProjectCreateEmpty(title="T", num_terms=2001)
    # terms_per_1k_words: 1..100
    with pytest.raises(ValidationError):
        ProjectCreateEmpty(title="T", terms_per_1k_words=0.5)
    with pytest.raises(ValidationError):
        ProjectCreateEmpty(title="T", terms_per_1k_words=150)


# ---------------------------------------------------------------------------
# ProcessRequest
# ---------------------------------------------------------------------------


def test_process_request_defaults() -> None:
    p = ProcessRequest()
    assert p.num_terms == 500
    assert p.terms_per_1k_words == 15.0
    assert p.translation_provider == "argos"
    assert p.processing_mode == "offline"
    assert p.use_ner is True


def test_process_request_provider_pattern() -> None:
    ProcessRequest(translation_provider="google")
    ProcessRequest(translation_provider="libretranslate")
    ProcessRequest(translation_provider="openai-gpt4o")
    with pytest.raises(ValidationError):
        ProcessRequest(translation_provider="bad provider!")


# ---------------------------------------------------------------------------
# TextSourceCreate
# ---------------------------------------------------------------------------


def test_text_source_valid() -> None:
    s = TextSourceCreate(name="Chapter 1", text="Hello world")
    assert s.name == "Chapter 1"
    assert s.text == "Hello world"


def test_text_source_strips() -> None:
    s = TextSourceCreate(name="  Ch1  ", text="  content  ")
    assert s.name == "Ch1"
    assert s.text == "content"


def test_text_source_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        TextSourceCreate(name="", text="x")
    with pytest.raises(ValidationError):
        TextSourceCreate(name="x", text="   ")


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------


def test_project_summary_from_attributes() -> None:
    class Row:
        id = "abc"
        title = "T"
        status = ProjectStatus.PENDING
        word_count = 10
        source_count = 2
        num_terms = 500
        created_at = datetime(2025, 1, 1)
        updated_at = datetime(2025, 1, 1)
        finished_at = None

    s = ProjectSummary.model_validate(Row())
    assert s.id == "abc"
    assert s.source_count == 2


def test_project_read_inherits_summary() -> None:
    class Row:
        id = "abc"
        title = "T"
        status = ProjectStatus.DONE
        word_count = 100
        source_count = 3
        num_terms = 500
        created_at = datetime(2025, 1, 1)
        updated_at = datetime(2025, 1, 2)
        finished_at = datetime(2025, 1, 2)
        translate_terms = True
        translate_definitions = False
        terms_per_1k_words = 15.0
        translation_provider = "libretranslate"
        processing_mode = "hybrid"      # ← این‌جا عوض شد
        use_spacy = True
        use_rake = True
        use_yake = False
        use_ner = True
        error_message = None
        started_at = datetime(2025, 1, 1)
        sources = []
        book_metadata = None

    s = ProjectRead.model_validate(Row())
    assert s.translation_provider == "libretranslate"
    assert s.processing_mode == "hybrid"
    assert s.terms_per_1k_words == 15.0
    assert s.sources == []
    assert s.book_metadata is None


def test_project_source_read_from_attributes() -> None:
    class Row:
        id = 1
        project_id = "abc"
        source_type = SourceType.FILE
        original_name = "ch1.pdf"
        path = "C:/x.pdf"
        word_count = 100
        order_index = 0
        included = True
        created_at = datetime(2025, 1, 1)
        updated_at = datetime(2025, 1, 1)

    s = ProjectSourceRead.model_validate(Row())
    assert s.source_type == SourceType.FILE
    assert s.original_name == "ch1.pdf"


def test_glossary_entry_read_from_attributes() -> None:
    class Row:
        id = 1
        project_id = "abc"
        english_term = "DNA"
        persian_term = "دی‌ان‌ای"
        english_definition = "A molecule."
        persian_definition = "یک مولکول."
        source = "In-Text"
        score = 0.9
        frequency = 3
        context = "DNA is a molecule."
        is_edited = False
        created_at = datetime(2025, 1, 1)
        updated_at = datetime(2025, 1, 1)

    s = GlossaryEntryRead.model_validate(Row())
    assert s.english_term == "DNA"
    assert s.frequency == 3


def test_glossary_entry_update_all_optional() -> None:
    u = GlossaryEntryUpdate()
    assert u.persian_term is None
    assert u.is_edited is None

    u = GlossaryEntryUpdate(persian_term="جدید", is_edited=True)
    assert u.persian_term == "جدید"


def test_setting_update_requires_value() -> None:
    SettingUpdate(value='"dark"')
    with pytest.raises(ValidationError):
        SettingUpdate()


def test_setting_read_from_attributes() -> None:
    class Row:
        key = "theme"
        value = '"dark"'
        updated_at = datetime(2025, 1, 1)

    s = SettingRead.model_validate(Row())
    assert s.key == "theme"