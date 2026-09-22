"""High-level translation service with caching, rate limiting, batching,
and a Wikipedia Persian-title fallback for proper names."""

from __future__ import annotations

from app.core.logging import get_logger
from app.pipeline.translation import cache
from app.pipeline.translation.argos import ArgosTranslatorProvider
from app.pipeline.translation.base import Translator
from app.pipeline.translation.google import GoogleTranslatorProvider
from app.pipeline.translation.libre import LibreTranslateProvider

log = get_logger("translation.service")

_PROVIDERS: dict[str, type[Translator]] = {
    "google": GoogleTranslatorProvider,
    "libretranslate": LibreTranslateProvider,
    "argos": ArgosTranslatorProvider,
}


def get_translator(provider: str) -> Translator:
    """Return a translator instance for the given provider name."""
    cls = _PROVIDERS.get(provider.lower(), GoogleTranslatorProvider)
    return cls()


def translate(
    text: str,
    provider: str = "google",
    source: str = "en",
    target: str = "fa",
) -> str:
    """Translate a single text with cache lookup."""
    if not text or not text.strip():
        return text

    cached = cache.get(text, source, target)
    if cached is not None:
        return cached

    try:
        translator = get_translator(provider)
        result = translator.translate(text, source=source, target=target)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Translation failed ({provider}): {exc}")
        return ""

    if not result or result.strip() == text.strip():
        return ""

    cache.set(text, source, target, result)
    return result


def _looks_like_proper_name(text: str) -> bool:
    """Heuristic: short, capitalized, no verbs → likely a proper name."""
    words = text.split()
    if not words or len(words) > 3:
        return False
    # First word must start with uppercase
    return words[0][0].isupper()


def _wikipedia_fallback(texts: list[str], target: str) -> list[str]:
    """For empty translations, try Persian Wikipedia titles.

    Only applies when target == "fa". Uses langlinks from English Wikipedia
    which is much more reliable for proper names than a translator.
    """
    if target != "fa":
        return ["" for _ in texts]

    from app.pipeline.definitions.wikipedia_langlinks import fetch_persian_title

    results: list[str] = []
    for t in texts:
        if not t or not t.strip():
            results.append("")
            continue
        title = None
        try:
            title = fetch_persian_title(t)
        except Exception as exc:  # noqa: BLE001
            log.debug(f"langlinks lookup failed for '{t}': {exc}")
        if title:
            log.info(f"Wikipedia fallback: '{t}' → '{title}'")
            results.append(title)
        else:
            results.append("")
    return results


def translate_many(
    texts: list[str],
    provider: str = "google",
    source: str = "en",
    target: str = "fa",
) -> list[str]:
    """Translate a batch of texts with cache + rate limiting + fallback."""
    if not texts:
        return []

    results: list[str | None] = [None] * len(texts)
    to_translate: list[tuple[int, str]] = []

    # Step 1: cache lookups
    for i, t in enumerate(texts):
        if not t or not t.strip():
            results[i] = t
            continue
        cached = cache.get(t, source, target)
        if cached is not None:
            results[i] = cached
            continue
        to_translate.append((i, t))

    if not to_translate:
        return [r if r is not None else "" for r in results]

    log.info(
        f"translate_many: {len(to_translate)}/{len(texts)} texts " f"require network ({provider})."
    )

    # Step 2: batch call
    try:
        translator = get_translator(provider)
        batch = [t for _, t in to_translate]
        translated_list = translator.translate_batch(batch, source=source, target=target)
        if len(translated_list) != len(batch):
            raise RuntimeError(
                f"Batch returned {len(translated_list)} items for {len(batch)} inputs"
            )
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Batch translation failed ({provider}): {exc}")
        for i, _ in to_translate:
            results[i] = ""
        translated_list = ["" for _ in to_translate]

    # Step 3: post-process and cache
    for (i, original), translated in zip(to_translate, translated_list):
        if not translated or translated.strip() == original.strip():
            results[i] = ""
        else:
            results[i] = translated
            cache.set(original, source, target, translated)

    # Step 4: Wikipedia fallback for empty results that look like proper names
    empty_originals = [
        (i, t) for i, t in to_translate if results[i] == "" and _looks_like_proper_name(t)
    ]
    if empty_originals:
        log.info(
            f"Trying Wikipedia fallback for {len(empty_originals)} proper-name-like "
            f"terms with empty translation."
        )
        fallbacks = _wikipedia_fallback([t for _, t in empty_originals], target)
        for (i, original), fb in zip(empty_originals, fallbacks):
            if fb:
                results[i] = fb
                cache.set(original, source, target, fb)

    return [r if r is not None else "" for r in results]
