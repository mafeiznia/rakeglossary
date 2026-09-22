"""LibreTranslate provider (self-hosted, ARM64-friendly) with true batch."""

from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.pipeline.translation.base import Translator
from app.pipeline.translation.rate_limiter import RateLimiter

log = get_logger("translation.libre")


class LibreTranslateProvider(Translator):
    name = "libretranslate"

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = (endpoint or settings.libre_translate_url).rstrip("/")
        self._limiter = RateLimiter(settings.translation_rate_limit)

    def _post(self, payload: dict) -> dict:
        delay = settings.translation_retry_base_delay
        max_retries = settings.translation_max_retries

        for attempt in range(max_retries + 1):
            try:
                self._limiter.acquire()
                r = httpx.post(
                    f"{self.endpoint}/translate",
                    json=payload,
                    timeout=settings.http_timeout,
                )
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as exc:
                if attempt >= max_retries:
                    log.warning(
                        f"LibreTranslate failed after " f"{max_retries + 1} attempts: {exc}"
                    )
                    raise
                log.info(f"LibreTranslate retry {attempt + 1}/{max_retries} " f"in {delay:.1f}s")
                time.sleep(delay)
                delay *= 2
        return {}

    def translate(self, text: str, source: str = "en", target: str = "fa") -> str:
        if not text or not text.strip():
            return text
        data = self._post(
            {
                "q": text,
                "source": source,
                "target": target,
                "format": "text",
            }
        )
        translated = data.get("translatedText", "")
        if not translated:
            raise RuntimeError("LibreTranslate returned empty response")
        return translated

    def translate_batch(
        self, texts: list[str], source: str = "en", target: str = "fa"
    ) -> list[str]:
        """True batch: LibreTranslate accepts an array via the `q` field."""
        indexed = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not indexed:
            return list(texts)

        batch_size = settings.translation_batch_size
        out: list[str] = list(texts)

        for start in range(0, len(indexed), batch_size):
            chunk = indexed[start : start + batch_size]
            payload = {
                "q": [t for _, t in chunk],
                "source": source,
                "target": target,
                "format": "text",
            }
            try:
                data = self._post(payload)
                results = data.get("translatedText", [])
                if not isinstance(results, list) or len(results) != len(chunk):
                    raise RuntimeError(
                        f"LibreTranslate returned {len(results)} items " f"for {len(chunk)} inputs"
                    )
                for (i, _), translated in zip(chunk, results):
                    out[i] = translated or ""
            except Exception as exc:  # noqa: BLE001
                log.warning(f"LibreTranslate batch chunk failed: {exc}")
                for i, _ in chunk:
                    out[i] = ""
        return out
