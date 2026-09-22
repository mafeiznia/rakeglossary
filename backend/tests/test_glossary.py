"""End-to-end tests for the glossary generation orchestrator."""
from __future__ import annotations

from unittest.mock import patch

from app.pipeline.glossary import (
    GlossaryEntry,
    GlossaryOptions,
    generate_glossary,
)
from app.pipeline.definitions.resolver import (
    DefinitionResult,
    DefinitionSource,
)


SAMPLE_TEXT = (
    "Photosynthesis is a biological process used by plants to convert light "
    "energy into chemical energy. DNA is a molecule that carries genetic "
    "information. Machine learning is a subfield of artificial intelligence. "
    "The mitochondrion is an organelle found in most eukaryotic cells."
)


def _fake_resolve(term: str, text: str) -> DefinitionResult:
    """Deterministic resolver for tests: always returns an in-text definition."""
    return DefinitionResult(
        text=f"Mocked definition of {term}.",
        source=DefinitionSource.IN_TEXT,
    )


def test_generate_glossary_from_raw_text() -> None:
    with patch("app.pipeline.glossary.resolve", side_effect=_fake_resolve), \
         patch("app.pipeline.glossary.translate", side_effect=lambda t, **kw: f"FA:{t}"):
        entries = generate_glossary(
            raw_text=SAMPLE_TEXT,
            options=GlossaryOptions(
                num_terms=5,
                translate_terms=True,
                translate_definitions=True,
                use_yake=False,
            ),
        )
    assert len(entries) > 0
    assert all(isinstance(e, GlossaryEntry) for e in entries)
    assert all(e.english_term for e in entries)
    assert all(e.persian_term.startswith("FA:") for e in entries)
    assert all(e.english_definition.startswith("Mocked") for e in entries)


def test_generate_glossary_without_translation() -> None:
    with patch("app.pipeline.glossary.resolve", side_effect=_fake_resolve):
        entries = generate_glossary(
            raw_text=SAMPLE_TEXT,
            options=GlossaryOptions(
                num_terms=3,
                translate_terms=False,
                translate_definitions=False,
                use_yake=False,
            ),
        )
    assert len(entries) > 0
    assert all(e.persian_term == "" for e in entries)
    assert all(e.persian_definition == "" for e in entries)


def test_generate_glossary_handles_empty_input() -> None:
    entries = generate_glossary(raw_text="")
    assert entries == []


def test_generate_glossary_handles_no_input() -> None:
    entries = generate_glossary()
    assert entries == []


def test_generate_glossary_computes_frequency_and_context() -> None:
    text = (
        "Photosynthesis is important. Photosynthesis drives most life on Earth. "
        "Plants use photosynthesis every day."
    )
    with patch("app.pipeline.glossary.resolve", side_effect=_fake_resolve):
        entries = generate_glossary(
            raw_text=text,
            options=GlossaryOptions(
                num_terms=10,
                translate_terms=False,
                translate_definitions=False,
                use_yake=False,
            ),
        )

    # دنبال entry تک‌واژه‌ی دقیق "Photosynthesis" بگرد
    photo = next(
        (e for e in entries if e.english_term.lower() == "photosynthesis"),
        None,
    )
    assert photo is not None, "Expected a single-word 'Photosynthesis' entry"
    assert photo.frequency >= 2
    assert photo.context

def test_generate_glossary_does_not_translate_definition_when_none() -> None:
    """When no definition is found, persian_definition must stay empty."""
    def _resolve_none(term: str, text: str) -> DefinitionResult:
        return DefinitionResult(
            text="Definition not found in text or online sources.",
            source=DefinitionSource.NONE,
        )

    with patch("app.pipeline.glossary.resolve", side_effect=_resolve_none), \
         patch("app.pipeline.glossary.translate", side_effect=lambda t, **kw: f"FA:{t}"):
        entries = generate_glossary(
            raw_text=SAMPLE_TEXT,
            options=GlossaryOptions(
                num_terms=3,
                translate_terms=True,
                translate_definitions=True,
                use_yake=False,
            ),
        )
    assert all(e.persian_definition == "" for e in entries)
    assert all(e.source == "None" for e in entries)