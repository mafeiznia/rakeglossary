"""Tests for the NLP keyword extraction pipeline."""
from __future__ import annotations

from app.pipeline.nlp.filters import is_valid, normalize
from app.pipeline.nlp.candidates import Candidate
from app.pipeline.nlp.extractor import extract_keywords


SAMPLE = (
    "Photosynthesis is a biological process used by plants, algae, and some "
    "bacteria to convert light energy into chemical energy. Chlorophyll is a "
    "green pigment that absorbs light. The Calvin cycle is part of photosynthesis. "
    "DNA and RNA are nucleic acids. AI and ML are subfields of computer science. "
    "The COVID-19 pandemic affected global health systems in 2020."
)


def test_normalize_collapses_whitespace() -> None:
    assert normalize("  hello   world  ") == "hello world"


def test_short_acronyms_are_kept() -> None:
    for term in ("AI", "ML", "UI", "UX"):
        assert is_valid(Candidate(term=term, source="spacy", raw_score=1.0))


def test_alphanumeric_terms_are_kept() -> None:
    for term in ("COVID-19", "Python 3", "3D printing"):
        assert is_valid(Candidate(term=term, source="spacy", raw_score=1.0))


def test_pure_digits_are_rejected() -> None:
    assert not is_valid(Candidate(term="2020", source="rake", raw_score=1.0))


def test_stopword_only_phrase_is_rejected() -> None:
    assert not is_valid(Candidate(term="the and of", source="rake", raw_score=1.0))


def test_extract_keywords_returns_results() -> None:
    kws = extract_keywords(SAMPLE, top_n=10, use_yake=False)
    assert len(kws) > 0
    assert all(k.term for k in kws)
    assert all(isinstance(k.score, float) for k in kws)


def test_extract_keywords_respects_top_n() -> None:
    kws = extract_keywords(SAMPLE, top_n=3, use_yake=False)
    assert len(kws) <= 3


def test_empty_text_returns_empty() -> None:
    assert extract_keywords("") == []
    assert extract_keywords("   ") == []
    
def test_extract_entities_returns_list() -> None:
    """NER should not crash on plain text."""
    from app.pipeline.nlp.candidates import extract_entities

    text = "Albert Einstein was born in Ulm, Germany. Marie Curie discovered radium in France."
    entities = extract_entities(text)
    assert isinstance(entities, list)
    # If spaCy model is present, we expect at least one entity
    # (test is tolerant to missing model)    