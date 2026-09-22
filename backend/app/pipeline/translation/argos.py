"""Argos Translate provider — fully offline neural translation.

Model files are downloaded on first use (~100 MB for en→fa) and cached
under the user's home directory. Subsequent runs are fully offline.

NOTE: Argos is a sentence-level translator. For very short inputs
(single words, 2-3 word phrases) it sometimes repeats the translation.
We apply a post-processing step to collapse those repetitions.
"""

from __future__ import annotations

import threading

from app.core.logging import get_logger
from app.pipeline.translation.base import Translator

log = get_logger("translation.argos")

_LOAD_LOCK = threading.Lock()
_LOADED = False


def _install_package_if_missing(from_code: str, to_code: str) -> None:
    import argostranslate.package

    installed = argostranslate.package.get_installed_packages()
    for p in installed:
        if p.from_code == from_code and p.to_code == to_code:
            log.info(f"Argos model {from_code}->{to_code} already installed.")
            return

    log.warning(
        f"Argos model {from_code}->{to_code} not found. " f"Downloading (~100 MB, one-time)..."
    )
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    target = next(
        (p for p in available if p.from_code == from_code and p.to_code == to_code),
        None,
    )
    if target is None:
        raise RuntimeError(f"No Argos model available for {from_code}->{to_code}.")

    log.info(f"Installing Argos package: {target} ...")
    argostranslate.package.install_from_path(target.download())
    log.info(f"Argos model {from_code}->{to_code} installed successfully.")


def _ensure_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    with _LOAD_LOCK:
        if _LOADED:
            return
        try:
            import argostranslate.translate  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "argostranslate is not installed. Run: pip install argostranslate"
            ) from exc

        _install_package_if_missing("en", "fa")
        _LOADED = True


def _collapse_repetitions(text: str) -> str:
    """Collapse repeated tokens produced by Argos for short inputs.

    Examples:
        "تبادل تبادل تبادل تبادل" → "تبادل"
        "شرکت شرکت" → "شرکت"
        "گفتگو مکالمه گفتگو مکالمه" → "گفتگو مکالمه"

    Long, natural text (e.g., translated definitions) is left untouched.
    """
    words = text.split()
    if len(words) < 2:
        return text

    # Case A: all words identical  (e.g., "X X X X X")
    if len(set(words)) == 1:
        return words[0]

    # Case B: 2-word pattern repeated many times
    #   "A B A B A B A B" → "A B"
    if len(words) >= 6 and len(words) % 2 == 0:
        half = len(words) // 2
        if words[:half] == words[half:]:
            words = words[:half]

    # Case C: same prefix repeated with a shared start
    #   "A A A B" → "A B"   (rare; only when first is short)
    #   We skip this to avoid false positives.

    # Case D: the same word repeated twice at the start, but the rest
    #   differs (e.g., "سقف سقف سقف اتاق" → "سقف اتاق")
    if len(words) >= 3 and words[0] == words[1] and words[0] == words[2]:
        # Drop consecutive duplicates from the head
        head = words[0]
        rest = [w for w in words[1:] if w != head]
        words = [head, *rest]

    return " ".join(words)


class ArgosTranslatorProvider(Translator):
    """Offline translator backed by Argos Translate (CTranslate2)."""

    name = "argos"

    def translate(self, text: str, source: str = "en", target: str = "fa") -> str:
        if not text or not text.strip():
            return text

        try:
            _ensure_loaded()
        except Exception as exc:
            log.warning(f"Argos model unavailable: {exc}")
            raise

        import argostranslate.translate

        # For very short inputs (1-2 words), wrap in dots so the sentence
        # model treats it as a complete sentence. Argos repeats much less
        # when the input looks like a sentence.
        stripped = text.strip()
        is_short = len(stripped.split()) <= 2
        to_translate = f". {stripped} ." if is_short else stripped

        try:
            result = argostranslate.translate.translate(to_translate, source, target)
        except Exception as exc:
            log.warning(f"Argos translate failed: {exc}")
            raise

        if not result or not result.strip():
            raise RuntimeError("Argos returned empty response")

        result = result.strip()

        # Strip the sentinel dots we added above
        if is_short:
            result = result.strip(" .،")

        # Collapse any remaining repetitions
        result = _collapse_repetitions(result)

        return result
