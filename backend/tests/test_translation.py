"""Tests for translation service."""

from __future__ import annotations

from unittest.mock import patch

from app.pipeline.translation import cache as cache_module
from app.pipeline.translation import translate, translate_many


def test_empty_text_returns_input() -> None:
    assert translate("") == ""
    assert translate("   ") == "   "


def test_google_translation_is_cached() -> None:
    cache_module._CACHE.clear()
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate",
        return_value="ترجمه‌شده",
    ) as mocked:
        first = translate("Hello", provider="google")
        second = translate("Hello", provider="google")
        assert first == second == "ترجمه‌شده"
        assert mocked.call_count == 1  # second call served from cache


def test_translation_failure_returns_empty_string() -> None:
    """When translation fails, the service returns an empty string so the
    UI can show a 'not translated' placeholder instead of the English text."""
    cache_module._CACHE.clear()
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate",
        side_effect=Exception("network down"),
    ):
        result = translate("Hello", provider="google")
        assert result == ""


def test_silent_failure_detected() -> None:
    """If the provider returns the input unchanged, treat it as failure."""
    cache_module._CACHE.clear()
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate",
        return_value="Hello",
    ):
        result = translate("Hello", provider="google")
        assert result == ""


def test_translate_many_uses_cache() -> None:
    cache_module._CACHE.clear()
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate_batch",
        return_value=["ترجمه۱", "ترجمه۲"],
    ) as mocked:
        r1 = translate_many(["Hello", "World"], provider="google")
        r2 = translate_many(["Hello", "World"], provider="google")
        assert r1 == ["ترجمه۱", "ترجمه۲"]
        assert r2 == r1
        assert mocked.call_count == 1  # second call served from cache


def test_translate_many_handles_empty_inputs() -> None:
    cache_module._CACHE.clear()
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate_batch",
        return_value=["ترجمه"],
    ) as mocked:
        result = translate_many(["Hello", "", "  "], provider="google")
        assert result == ["ترجمه", "", "  "]
        # Only non-empty string reaches the provider
        called_args = mocked.call_args[0][0]
        assert called_args == ["Hello"]


def test_translate_many_returns_empty_on_failure() -> None:
    """When batch translation fails and no Wikipedia fallback exists,
    the service returns empty strings."""
    cache_module._CACHE.clear()
    with (
        patch(
            "app.pipeline.translation.google.GoogleTranslatorProvider.translate_batch",
            side_effect=Exception("network down"),
        ),
        patch(
            "app.pipeline.definitions.wikipedia_langlinks.fetch_persian_title",
            return_value=None,
        ),
    ):
        # Use non-proper-name terms so Wikipedia fallback isn't triggered
        result = translate_many(["something", "else"], provider="google")
        assert result == ["", ""]


def test_argos_provider_registered() -> None:
    """Argos should be listed among available providers."""
    from app.pipeline.translation.service import _PROVIDERS

    assert "argos" in _PROVIDERS


def test_argos_empty_input_returns_unchanged() -> None:
    """Empty strings are passed through without invoking the model."""
    from app.pipeline.translation.argos import ArgosTranslatorProvider

    provider = ArgosTranslatorProvider()
    assert provider.translate("") == ""
    assert provider.translate("   ") == "   "


# ---------------------------------------------------------------------------
# Bug 6: _looks_like_proper_name was too permissive
# ---------------------------------------------------------------------------


def test_looks_like_proper_name_rejects_common_words() -> None:
    """Regression: sentences starting with common stopwords like 'The' or
    'A' must not be classified as proper names.

    Before the fix, any short text starting with an uppercase letter was
    considered a proper name, causing pointless Wikipedia lookups during
    the translation fallback.
    """
    from app.pipeline.translation.service import _looks_like_proper_name

    # These start with a capital but are not proper names:
    assert _looks_like_proper_name("The house") is False
    assert _looks_like_proper_name("A man") is False
    assert _looks_like_proper_name("An apple") is False
    assert _looks_like_proper_name("This thing") is False
    assert _looks_like_proper_name("That person") is False


def test_looks_like_proper_name_accepts_real_names() -> None:
    """Regression: real proper names must still be detected."""
    from app.pipeline.translation.service import _looks_like_proper_name

    assert _looks_like_proper_name("Yumiko") is True
    assert _looks_like_proper_name("Kagoshima") is True
    assert _looks_like_proper_name("New York") is True
    assert _looks_like_proper_name("Haruki Murakami") is True


def test_looks_like_proper_name_rejects_lowercase_start() -> None:
    """Regression: lowercase-starting strings were already rejected."""
    from app.pipeline.translation.service import _looks_like_proper_name

    assert _looks_like_proper_name("hello world") is False
    assert _looks_like_proper_name("some random words") is False


def test_looks_like_proper_name_rejects_long_phrases() -> None:
    """Regression: phrases longer than 3 words were already rejected."""
    from app.pipeline.translation.service import _looks_like_proper_name

    assert _looks_like_proper_name("One two three four") is False
    assert _looks_like_proper_name("A b c d e") is False
