"""Tests for definition resolution (classic layered fallback)."""
from __future__ import annotations

from unittest.mock import patch

from app.pipeline.definitions import (
    DefinitionSource,
    resolve,
    resolve_classic,
)
from app.pipeline.definitions.in_text import find_in_text


# ---------------------------------------------------------------------------
# in-text layer
# ---------------------------------------------------------------------------


def test_in_text_simple_pattern() -> None:
    text = "Photosynthesis is a process used by plants to convert light into energy."
    assert find_in_text("Photosynthesis", text) is not None


def test_in_text_refers_to_pattern() -> None:
    text = "RAKE refers to a keyword extraction algorithm based on word co-occurrence."
    assert find_in_text("RAKE", text) is not None


def test_in_text_missing_returns_none() -> None:
    assert find_in_text("NonexistentTerm", "Short text without definitions.") is None


# ---------------------------------------------------------------------------
# resolve (classic)
# ---------------------------------------------------------------------------


def test_resolver_prefers_in_text() -> None:
    text = "Photosynthesis is a process used by plants to make food from sunlight."
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value=None,
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value=None,
    ):
        result = resolve_classic("Photosynthesis", text)
        assert result.source is DefinitionSource.IN_TEXT


def test_resolver_falls_back_to_wikipedia() -> None:
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value="A mocked Wikipedia extract.",
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value=None,
    ):
        result = resolve_classic("SomeTerm", "text without definition")
        assert result.source is DefinitionSource.WIKIPEDIA
        assert "mocked" in result.text


def test_resolver_falls_back_to_wordnet() -> None:
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value=None,
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value="A common noun definition.",
    ):
        result = resolve_classic("something", "text without definitions")
        assert result.source is DefinitionSource.WORDNET
        assert "common noun" in result.text


def test_resolver_returns_none_source_when_all_fail() -> None:
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value=None,
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value=None,
    ):
        result = resolve_classic("SomeTerm", "text without definition")
        assert result.source is DefinitionSource.NONE


def test_resolver_wikipedia_priority_over_wordnet() -> None:
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value="From Wikipedia.",
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value="From WordNet.",
    ) as wn_mock:
        result = resolve_classic("DNA", "text without definitions")
        assert result.source is DefinitionSource.WIKIPEDIA
        assert "Wikipedia" in result.text
        wn_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Backwards-compatible alias `resolve`
# ---------------------------------------------------------------------------


def test_resolve_alias_uses_classic() -> None:
    text = "Photosynthesis is a process used by plants."
    with patch(
        "app.pipeline.definitions.wikipedia.fetch",
        return_value=None,
    ), patch(
        "app.pipeline.definitions.wordnet.fetch",
        return_value=None,
    ):
        result = resolve("Photosynthesis", text)
        assert result.source is DefinitionSource.IN_TEXT


# ---------------------------------------------------------------------------
# WordNet layer
# ---------------------------------------------------------------------------


def test_wordnet_returns_definition_for_common_word() -> None:
    from app.pipeline.definitions.wordnet import fetch

    result = fetch("dog")
    if result is None:
        import pytest
        pytest.skip("WordNet data not available in this environment.")
    assert isinstance(result, str)
    assert len(result) > 10


def test_wordnet_returns_none_for_made_up_word() -> None:
    from app.pipeline.definitions.wordnet import fetch

    assert fetch("Qwertyzxcvbnm") is None


def test_wordnet_returns_none_for_empty() -> None:
    from app.pipeline.definitions.wordnet import fetch

    assert fetch("") is None
    assert fetch("   ") is None


def test_wordnet_returns_none_for_non_alpha() -> None:
    from app.pipeline.definitions.wordnet import fetch

    assert fetch("123") is None
    assert fetch("AI-2024") is None


def test_wordnet_rejects_long_phrases() -> None:
    from app.pipeline.definitions.wordnet import fetch

    assert fetch("this is a very long phrase") is None