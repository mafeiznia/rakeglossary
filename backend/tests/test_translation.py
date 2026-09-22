"""Tests for translation service."""
from __future__ import annotations

from unittest.mock import patch

from app.pipeline.translation import translate, translate_many
from app.pipeline.translation import cache as cache_module


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
    with patch(
        "app.pipeline.translation.google.GoogleTranslatorProvider.translate_batch",
        side_effect=Exception("network down"),
    ), patch(
        "app.pipeline.definitions.wikipedia_langlinks.fetch_persian_title",
        return_value=None,
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