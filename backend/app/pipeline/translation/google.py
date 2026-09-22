"""Google translator via deep-translator with rate limiting + retry."""

from __future__ import annotations

import time

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    RequestError,
    ServerException,
    TooManyRequests,
    TranslationNotFound,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.pipeline.translation.base import Translator
from app.pipeline.translation.rate_limiter import RateLimiter

log = get_logger("translation.google")

# Errors that are worth retrying (network hiccups, rate limits)
_RETRYABLE = (RequestError, TooManyRequests, ServerException, ConnectionError)


class GoogleTranslatorProvider(Translator):
    name = "google"

    def __init__(self) -> None:
        self._limiter = RateLimiter(settings.translation_rate_limit)

    def _call(self, fn, *args, **kwargs):
        """Rate-limited call with exponential backoff on retryable errors."""
        delay = settings.translation_retry_base_delay
        max_retries = settings.translation_max_retries

        for attempt in range(max_retries + 1):
            try:
                self._limiter.acquire()
                return fn(*args, **kwargs)
            except _RETRYABLE as exc:
                if attempt >= max_retries:
                    log.warning(
                        f"Google translation failed after " f"{max_retries + 1} attempts: {exc}"
                    )
                    raise
                log.info(
                    f"Google retry {attempt + 1}/{max_retries} "
                    f"in {delay:.1f}s: {type(exc).__name__}"
                )
                time.sleep(delay)
                delay *= 2
        return None

    def translate(self, text: str, source: str = "en", target: str = "fa") -> str:
        if not text or not text.strip():
            return text
        translator = GoogleTranslator(source=source, target=target)
        try:
            result = self._call(translator.translate, text)
        except TranslationNotFound:
            return ""
        if result is None:
            return ""
        return result

    def translate_batch(
        self, texts: list[str], source: str = "en", target: str = "fa"
    ) -> list[str]:
        """Translate a list of texts, applying the rate limiter to each."""
        # Pre-filter so empty strings skip the network entirely
        out: list[str] = list(texts)
        for i, t in enumerate(texts):
            if not t or not t.strip():
                continue
            try:
                out[i] = self.translate(t, source=source, target=target)
            except Exception as exc:  # noqa: BLE001
                log.warning(f"Batch item failed: {exc}")
                out[i] = ""
        return out
