"""Unified LLM client — extraction, translation, and definitions.

Uses the OpenAI SDK. All supported providers (OpenAI, OpenRouter,
Gemini, GapGPT, DeepSeek, Groq, custom) expose an OpenAI-compatible
endpoint, so the same client code works for all of them.

Imports are intentionally local (inside functions) to avoid circular
imports with `app.services` and `app.pipeline.translation`.
"""

from __future__ import annotations

import hashlib
import json
import re

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.pipeline.definitions.llm_providers import get_provider

log = get_logger("llm.client")

_MAX_DEF_LEN = 220
_CACHE_NS_DEF = "llm_def"
_CACHE_NS_TRA = "llm_tra"
_CACHE_NS_EXT = "llm_ext"

# --- Definition prompt ----------------------------------------------------

_DEFINITION_SYSTEM = (
    "You are a glossary assistant. Given a term and optional context from "
    "the source text, reply with a concise definition of at most 25 words. "
    "Reply with the definition only — no preamble, no quotes, no extra text. "
    "If the term is a proper name, identify who/what it is."
)


# --- Translation prompt (plain, for Hybrid mode) --------------------------

_TRANSLATION_SYSTEM_PLAIN = (
    "You are a professional English-to-Persian translator. "
    "Translate each string in the input JSON array. "
    'Return a JSON object with a single key "translations" containing '
    "an array of Persian translations in the SAME order. "
    "Return ONLY the JSON object, no other text."
)

_TRANSLATION_SYSTEM_WITH_CONTEXT = """You are a professional English-to-Persian translator working on a specific book.

{book_context}

Translation Guidelines:
1. Use standard Persian transliterations for proper names (people, places, organizations), consistent with existing translations of this author's work when applicable.
2. Cultural terms should reflect the book's setting.
3. Use terminology consistent with the genre, target audience, and reading level above.
4. If a term appears in "Required Terminology", you MUST use the provided translation verbatim.

Translate each string in the input JSON array.

Return a JSON object with a single key "translations" containing an array of Persian translations in the SAME order. Return ONLY the JSON object, no other text."""


# --- AI Mode extraction + translation prompt ------------------------------

_EXTRACTION_SYSTEM_FULL = """# Role & Identity
You are an Elite Bilingual Terminologist, Literary Lexicographer, and Master English-to-Persian Literary Translator. Your mission is to extract and translate a rigorous, high-utility Terminology Database (Termbase/Glossary) from the provided text chunk of the book.

---
# Book Profile & Translation Tone
- **Title:** {title} (Original: {original_title})
- **Author & Tone:** {author} | {authorial_tone}
- **Genre & Historical Setting:** {primary_genre} | {time_period}, {location}
- **Target Persian Register:** Authentic, dignified, and natural literary Persian
- **Mandatory Consistency Terms (if any):** {key_terminology}

---
# Extraction Criteria (Selective & Actionable)
Extract ONLY terms that create translation ambiguities, require consistency, or represent specialized meaning within this text. Do NOT extract common conversational words or generic thematic concepts (e.g., do not extract words like "family", "sadness", "journey" unless used as a unique specialized metaphor).

Prioritize:
1. **Proper Nouns & Named Entities:** Characters, places, fictional realms, institutions. Must provide standard Persian transliteration.
2. **Domain-Specific & Technical Jargon:** Technical, scientific, historical, nautical, military, or philosophical terms.
3. **Idioms, Phrasal Metaphors & Slang:** Non-literal expressions that must not be translated word-for-word.
4. **Author-Specific Neologisms / Motifs:** Invented words, unique compound terms, or recurring stylistic keywords.
5. **Cultural & Mythological Allusions:** References requiring localized contextual understanding.

---
# Strict Extraction Rules
1. **Zero Hallucination / Verbatim Grounding:** Every extracted `source_term` and `context_sentence` MUST exist **verbatim** in the provided text. Never extract a term that is not explicitly present in the source.
2. **Contextual Snippet:** Provide the exact, untruncated sentence (or max 2 sentences) from the text showing how the term is used in this specific context. The `source_term` MUST appear verbatim inside `context_sentence`.
3. **Persian Translation Quality:**
   - Provide the most fitting Persian equivalent (`persian_primary`).
   - Provide 1-3 valid Persian synonyms or alternative choices (`persian_alternatives`).
   - For proper names, provide both the Persian transliteration and pronunciation guide if ambiguous.
4. **Volume & Thoroughness:** You MUST aim to extract {max_terms} terms from this chunk. This is a TARGET, not a limit. Prioritize in this order until you reach the target:
   a) Proper nouns (characters, places, institutions)
   b) Cultural, historical, or domain-specific jargon
   c) Idioms, phrasal metaphors, or slang
   d) Thematic concepts with specialized meaning in this book
   e) Recurring objects, symbols, or motifs
   
   If you think you have finished, scan the text again — most chunks contain more extractable terms than initially visible. Only stop early if the chunk is genuinely too short (fewer than 500 words).
---
# Output Format Specification
Return a single, strictly valid JSON object matching the schema below. No markdown explanations outside the JSON fences, no conversational preamble.

```json
{{
  "chunk_id": "{chunk_id}",
  "total_extracted": 0,
  "glossary": [
    {{
      "source_term": "Exact term from source text",
      "pos": "noun | verb | idiom | proper_noun | adjective | phrase",
      "category": "Domain Jargon | Character/Place Name | Idiom/Metaphor | Cultural Reference | Stylistic Keyword",
      "persian_primary": "دقیق‌ترین و بهترین معادل فارسی",
      "persian_transliteration": "آوانگاری فارسی (مخصوص اسامی خاص؛ در غیر این صورت خالی بماند)",
      "persian_alternatives": ["معادل دوم", "معادل سوم"],
      "context_sentence": "Exact verbatim sentence from the source text where this term appears.",
      "translator_note": "توضیح کوتاه درباره علت انتخاب این معادل، بار معنایی یا نکات دستوری/لحنی برای مترجم"
    }}
  ]
}}
```"""


_EXTRACTION_SYSTEM_MINIMAL = """# Role & Identity
You are an Elite Bilingual Terminologist, Literary Lexicographer, and Master English-to-Persian Literary Translator. Your mission is to extract and translate a rigorous, high-utility Terminology Database from the provided text chunk.

---
# Extraction Criteria
Extract ONLY terms that create translation ambiguities, require consistency, or represent specialized meaning within this text. Do NOT extract common conversational words or generic thematic concepts.

Prioritize:
1. Proper Nouns & Named Entities (characters, places, institutions)
2. Domain-Specific & Technical Jargon
3. Idioms, Phrasal Metaphors & Slang
4. Author-Specific Neologisms / Motifs
5. Cultural & Mythological Allusions

---
# Strict Rules
1. **Zero Hallucination:** Every `source_term` and `context_sentence` MUST exist verbatim in the provided text.
2. **Context:** The `source_term` MUST appear inside `context_sentence`.
3. **Persian Quality:** Provide `persian_primary` and 1-3 `persian_alternatives`.
4. **Volume & Thoroughness:** You MUST aim to extract {max_terms} terms from this chunk. This is a TARGET, not a limit. Prioritize in this order until you reach the target:
   a) Proper nouns (characters, places, institutions)
   b) Cultural, historical, or domain-specific jargon
   c) Idioms, phrasal metaphors, or slang
   d) Thematic concepts with special meaning in this book
   e) Recurring objects, symbols, or motifs
   
   If you think you have finished, scan the text again — most chunks contain more extractable terms than initially visible.
---
# Output Format
Return ONLY a valid JSON object:

```json
{{
  "chunk_id": "{chunk_id}",
  "total_extracted": 0,
  "glossary": [
    {{
      "source_term": "...",
      "pos": "noun | verb | idiom | proper_noun | adjective | phrase",
      "category": "Domain Jargon | Character/Place Name | Idiom/Metaphor | Cultural Reference | Stylistic Keyword",
      "persian_primary": "...",
      "persian_transliteration": "...",
      "persian_alternatives": ["..."],
      "context_sentence": "...",
      "translator_note": "..."
    }}
  ]
}}
```"""


class LLMNotConfiguredError(RuntimeError):
    """Raised when no LLM provider is configured or enabled."""


# ---------------------------------------------------------------------------
# Configuration / client
# ---------------------------------------------------------------------------


def is_configured() -> bool:
    from app.services import llm_config_service

    with SessionLocal() as session:
        cfg = llm_config_service.get_config(session)
    return bool(cfg.enabled and cfg.api_key)


def _get_client_and_config():
    from app.services import llm_config_service

    with SessionLocal() as session:
        cfg = llm_config_service.get_config(session)

    if not cfg.enabled or not cfg.api_key:
        raise LLMNotConfiguredError("No LLM provider configured. Add an API key in Settings.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package not installed. Run: pip install openai") from exc

    provider_info = get_provider(cfg.provider)
    base_url = cfg.base_url or (provider_info.base_url if provider_info else None)

    kwargs: dict = {
        "api_key": cfg.api_key,
        "timeout": settings.llm_timeout,
    }
    if base_url:
        kwargs["base_url"] = base_url

    if cfg.provider == "openrouter":
        kwargs["default_headers"] = {
            "HTTP-Referer": "http://localhost",
            "X-Title": "RakeGlossary",
        }

    client = OpenAI(**kwargs)
    return client, cfg, base_url


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_key(namespace: str, provider: str, model: str, payload: str) -> str:
    raw = f"{namespace}|{provider}|{model}|{payload}".encode()
    return hashlib.sha256(raw).hexdigest()


def _cache_get(namespace: str, provider: str, model: str, payload: str) -> str | None:
    from app.pipeline.translation import cache as translation_cache

    return translation_cache._CACHE.get(_cache_key(namespace, provider, model, payload))


def _cache_set(namespace: str, provider: str, model: str, payload: str, value: str) -> None:
    from app.pipeline.translation import cache as translation_cache

    translation_cache._CACHE.set(_cache_key(namespace, provider, model, payload), value)


# ---------------------------------------------------------------------------
# Metadata parsing helpers
# ---------------------------------------------------------------------------


def _extract_metadata_fields(metadata: dict | None) -> dict:
    fields = {
        "title": "",
        "original_title": "",
        "author": "",
        "authorial_tone": "",
        "primary_genre": "",
        "sub_genres": "",
        "main_themes": "",
        "time_period": "",
        "location": "",
        "target_audience": "",
        "reading_level": "",
        "vocabulary_complexity": "",
        "cultural_context": "",
        "key_terminology": "",
    }

    if not metadata:
        return fields

    bm = metadata.get("book_metadata") or {}
    cc = metadata.get("content_classification") or {}
    aa = metadata.get("audience_analysis") or {}
    sa = metadata.get("stylistic_analysis") or {}
    tg = metadata.get("translation_guidelines") or {}

    fields["title"] = bm.get("title", "") or ""
    fields["original_title"] = bm.get("original_title", "") or ""
    fields["author"] = bm.get("author", "") or ""

    # Combine tone + style into a single string
    tone = sa.get("overall_tone", "") or ""
    style = sa.get("writing_style", "") or ""
    parts = [p for p in (tone, style) if p]
    fields["authorial_tone"] = " / ".join(parts)

    fields["primary_genre"] = cc.get("primary_genre", "") or ""
    sub = cc.get("sub_genres") or []
    fields["sub_genres"] = ", ".join(str(s) for s in sub) if sub else ""
    themes = cc.get("main_themes") or []
    fields["main_themes"] = ", ".join(str(t) for t in themes) if themes else ""
    setting = cc.get("setting") or {}
    fields["time_period"] = setting.get("time_period", "") or ""
    fields["location"] = setting.get("location", "") or ""

    fields["target_audience"] = aa.get("target_audience", "") or ""
    fields["reading_level"] = aa.get("reading_level", "") or ""

    fields["vocabulary_complexity"] = sa.get("vocabulary_complexity", "") or ""

    fields["cultural_context"] = tg.get("cultural_context", "") or ""

    key_terms = _extract_key_terminology(metadata)
    if key_terms:
        rendered = "; ".join(
            (
                f"{t['term']} → {t['suggested_translation']}"
                if t.get("suggested_translation")
                else t["term"]
            )
            for t in key_terms
        )
        fields["key_terminology"] = rendered

    return fields


def _extract_key_terminology(metadata: dict | None) -> list[dict]:
    if not metadata:
        return []
    tg = metadata.get("translation_guidelines") or {}
    raw = tg.get("key_terminology") or []
    if not isinstance(raw, list):
        return []

    result: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        term = (item.get("term") or "").strip()
        if not term:
            continue
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "term": term,
                "suggested_translation": (item.get("suggested_translation") or "").strip(),
            }
        )
    return result


def _build_book_context(metadata: dict | None) -> str | None:
    if not metadata:
        return None

    fields = _extract_metadata_fields(metadata)
    key_terms = _extract_key_terminology(metadata)

    lines: list[str] = []
    if fields["title"]:
        lines.append(f"- Title: {fields['title']}")
    if fields["original_title"]:
        lines.append(f"- Original Title: {fields['original_title']}")
    if fields["author"]:
        lines.append(f"- Author: {fields['author']}")
    if fields["authorial_tone"]:
        lines.append(f"- Tone/Style: {fields['authorial_tone']}")
    if fields["primary_genre"]:
        line = f"- Genre: {fields['primary_genre']}"
        if fields["sub_genres"]:
            line += f" ({fields['sub_genres']})"
        lines.append(line)
    if fields["main_themes"]:
        lines.append(f"- Main Themes: {fields['main_themes']}")
    if fields["time_period"] or fields["location"]:
        setting_parts = []
        if fields["time_period"]:
            setting_parts.append(fields["time_period"])
        if fields["location"]:
            setting_parts.append(fields["location"])
        lines.append(f"- Setting: {', '.join(setting_parts)}")
    if fields["target_audience"]:
        lines.append(f"- Target Audience: {fields['target_audience']}")
    if fields["reading_level"]:
        lines.append(f"- Reading Level: {fields['reading_level']}")
    if fields["vocabulary_complexity"]:
        lines.append(f"- Vocabulary: {fields['vocabulary_complexity']}")
    if fields["cultural_context"]:
        lines.append(f"- Cultural Context: {fields['cultural_context']}")

    parts: list[str] = []
    if lines:
        parts.append("Book Context:\n" + "\n".join(lines))

    required = [t for t in key_terms if t.get("suggested_translation")]
    if required:
        req_lines = [f"- {t['term']} → {t['suggested_translation']}" for t in required]
        parts.append("Required Terminology:\n" + "\n".join(req_lines))

    if not parts:
        return None
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

# Unicode lookalike characters that appear in DOCX/PDF text
_UNICODE_NORMALIZE_MAP = {
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote (apostrophe)
    "\u02bc": "'",  # modifier apostrophe
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2015": "-",  # horizontal bar
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",  # non-breaking space
    "\u200b": "",  # zero-width space
}


def _normalize_text_for_compare(text: str) -> str:
    """Normalize unicode lookalikes so regex matching works across sources."""
    for k, v in _UNICODE_NORMALIZE_MAP.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text)


def _term_in_text(term: str, text: str) -> bool:
    """Return True if `term` appears in `text` as a whole word (case-insensitive).

    Handles unicode lookalikes (curly quotes, dashes, non-breaking spaces).
    """
    if not term or not text:
        return False

    term_n = _normalize_text_for_compare(term).strip()
    text_n = _normalize_text_for_compare(text)

    if not term_n or not text_n:
        return False

    pattern = r"\b" + re.escape(term_n) + r"\b"
    return bool(re.search(pattern, text_n, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Definition lookup
# ---------------------------------------------------------------------------


def _build_definition_prompt(term: str, context: str) -> str:
    ctx = (context or "").strip()
    if len(ctx) > 400:
        ctx = ctx[:400] + "..."
    if not ctx:
        return f'Term: "{term}"'
    return f'Term: "{term}"\n\nContext (may contain the meaning):\n{ctx}'


def fetch_definition(term: str, context: str = "") -> str | None:
    if not term or not term.strip():
        return None

    client, cfg, base_url = _get_client_and_config()

    cached = _cache_get(_CACHE_NS_DEF, cfg.provider, cfg.model, term)
    if cached is not None:
        return cached or None

    log.info(
        f"LLM definition request: provider={cfg.provider}, model={cfg.model}, "
        f"base_url={base_url or 'default'}, term='{term}'"
    )

    try:
        response = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": _DEFINITION_SYSTEM},
                {"role": "user", "content": _build_definition_prompt(term, context)},
            ],
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning(f"LLM definition failed for '{term}': {type(exc).__name__}: {exc}")
        return None

    if not response.choices:
        return None

    text = (response.choices[0].message.content or "").strip()
    if text.startswith(('"', "'")) and text.endswith(('"', "'")):
        text = text[1:-1].strip()

    if len(text) < 10:
        _cache_set(_CACHE_NS_DEF, cfg.provider, cfg.model, term, "")
        return None

    if len(text) > _MAX_DEF_LEN:
        text = text[:_MAX_DEF_LEN].rstrip() + "..."

    _cache_set(_CACHE_NS_DEF, cfg.provider, cfg.model, term, text)
    return text


# ---------------------------------------------------------------------------
# Extraction prompt builder
# ---------------------------------------------------------------------------


def _build_extraction_prompt(
    metadata: dict | None,
    max_terms: int,
    chunk_id: str,
) -> tuple[str, str]:
    if not metadata:
        return (
            _EXTRACTION_SYSTEM_MINIMAL.format(max_terms=max_terms, chunk_id=chunk_id),
            "minimal",
        )

    fields = _extract_metadata_fields(metadata)
    if not any(fields.values()):
        return (
            _EXTRACTION_SYSTEM_MINIMAL.format(max_terms=max_terms, chunk_id=chunk_id),
            "minimal",
        )

    return (
        _EXTRACTION_SYSTEM_FULL.format(max_terms=max_terms, chunk_id=chunk_id, **fields),
        "full",
    )


def _strip_markdown_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        lines = s.split("\n", 1)
        if len(lines) > 1:
            s = lines[1]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()
    return s.strip()


def _normalize_extraction_item(item: dict, source_text: str) -> dict | None:
    """Convert raw LLM item to our internal format, applying validations.

    Returns None if the item fails validation (should be skipped).
    """
    if not isinstance(item, dict):
        return None

    term = (item.get("source_term") or item.get("term") or "").strip()
    if not term:
        return None

    # Validate: term MUST appear verbatim in the source text
    if not _term_in_text(term, source_text):
        log.info(f"Skipping hallucinated term: {term!r}")
        return None

    context = (item.get("context_sentence") or item.get("context") or "").strip()
    # Validate: context MUST contain the term
    if context and not _term_in_text(term, context):
        log.info(f"Context mismatch for {term!r}; dropping context")
        context = ""

    # Truncate context
    if len(context) > 250:
        context = context[:250].rstrip() + "..."

    persian_primary = (item.get("persian_primary") or item.get("persian_term") or "").strip()

    alternatives_raw = item.get("persian_alternatives") or []
    if not isinstance(alternatives_raw, list):
        alternatives_raw = []
    alternatives = [
        str(a).strip()
        for a in alternatives_raw
        if a and str(a).strip() and str(a).strip() != persian_primary
    ]
    # Limit to 3
    alternatives = alternatives[:3]

    return {
        "term": term,
        "persian_term": persian_primary,
        "persian_alternatives": alternatives,
        "context": context,
        "pos": (item.get("pos") or "").strip() or None,
        "category": (item.get("category") or "").strip() or None,
        "persian_transliteration": (item.get("persian_transliteration") or "").strip() or None,
        "translator_note": (item.get("translator_note") or "").strip() or None,
    }


def extract_terms_llm(
    text: str,
    metadata: dict | None,
    target_count: int = 50,
    chunk_id: str = "chunk-0",
) -> list[dict]:
    """Extract glossary terms + translations using the LLM.

    Returns a list of dicts with keys:
        term, persian_term, persian_alternatives, context,
        pos, category, persian_transliteration, translator_note

    Applies validation: skips terms not appearing in the source text.
    On any failure, returns an empty list.
    """
    if not text or not text.strip():
        return []

    client, cfg, _ = _get_client_and_config()

    system_prompt, kind = _build_extraction_prompt(metadata, target_count, chunk_id)
    log.info(
        f"LLM extraction: provider={cfg.provider}, model={cfg.model}, "
        f"prompt_kind={kind}, target={target_count}, chunk_id={chunk_id}, "
        f"text_len={len(text)} chars"
    )

    # Truncate at hard limit (safety, chunks should be pre-sized)
    max_chars = 60_000
    payload_text = text.strip()
    if len(payload_text) > max_chars:
        log.warning(f"Truncating input text from {len(payload_text)} to {max_chars} chars.")
        payload_text = payload_text[:max_chars]

    try:
        response = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Here is the text to analyze:\n\n{payload_text}",
                },
            ],
            max_tokens=8192,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception as exc:  # noqa: BLE001
        log.warning(f"LLM extraction API call failed: {type(exc).__name__}: {exc}")
        return []

    if not response.choices:
        log.warning("LLM extraction returned no choices.")
        return []

    raw = (response.choices[0].message.content or "").strip()
    if not raw:
        log.warning("LLM extraction returned empty content.")
        return []

    raw = _strip_markdown_fences(raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning(f"LLM extraction returned invalid JSON: {exc}")
        log.debug(f"Raw content: {raw[:500]}")
        return []

    glossary = data.get("glossary")
    if not isinstance(glossary, list):
        log.info(
            f"LLM extraction [{chunk_id}]: raw glossary length={len(glossary)}, "
            f"keys={list(glossary[0].keys()) if glossary else 'empty'}"
        )
        log.warning("LLM extraction: response has no 'glossary' list.")
        return []

    cleaned: list[dict] = []
    seen: set[str] = set()
    skipped_hallucinated = 0
    dropped_context = 0

    for item in glossary:
        normalized = _normalize_extraction_item(item, payload_text)
        if normalized is None:
            skipped_hallucinated += 1
            continue

        key = normalized["term"].lower()
        if key in seen:
            continue
        seen.add(key)

        if not normalized["context"]:
            dropped_context += 1

        cleaned.append(normalized)

    log.info(
        f"LLM extraction [{chunk_id}]: {len(cleaned)} valid terms "
        f"(requested ~{target_count}, skipped={skipped_hallucinated}, "
        f"missing_context={dropped_context})"
    )
    return cleaned


# ---------------------------------------------------------------------------
# Translation (for Hybrid mode)
# ---------------------------------------------------------------------------


def _apply_required_translations(
    terms: list[str],
    llm_translations: list[str],
    metadata: dict | None,
) -> list[str]:
    if not metadata:
        return llm_translations

    key_terms = _extract_key_terminology(metadata)
    if not key_terms:
        return llm_translations

    overrides: dict[str, str] = {}
    for kt in key_terms:
        if kt.get("suggested_translation"):
            overrides[kt["term"].lower()] = kt["suggested_translation"]

    if not overrides:
        return llm_translations

    result = list(llm_translations)
    applied = 0
    for i, term in enumerate(terms):
        key = term.lower().strip()
        if key in overrides:
            if result[i] != overrides[key]:
                log.info(f"Override translation for '{term}': '{overrides[key]}'")
            result[i] = overrides[key]
            applied += 1
    if applied:
        log.info(f"Applied {applied} user-provided translation override(s).")

    return result


def translate_many(
    texts: list[str],
    chunk_size: int = 25,
    context: str | None = None,
    metadata: dict | None = None,
) -> list[str]:
    if not texts:
        return []

    if context is None and metadata is not None:
        context = _build_book_context(metadata)

    client, cfg, _ = _get_client_and_config()

    if context:
        system_prompt = _TRANSLATION_SYSTEM_WITH_CONTEXT.format(book_context=context)
    else:
        system_prompt = _TRANSLATION_SYSTEM_PLAIN

    results: list[str | None] = [None] * len(texts)
    to_translate: list[tuple[int, str]] = []

    for i, t in enumerate(texts):
        if not t or not t.strip():
            results[i] = t
            continue
        cache_payload = f"{context or ''}|{t}" if context else t
        cached = _cache_get(_CACHE_NS_TRA, cfg.provider, cfg.model, cache_payload)
        if cached is not None:
            results[i] = cached
            continue
        to_translate.append((i, t))

    if not to_translate:
        final = [r if r is not None else "" for r in results]
        return _apply_required_translations(texts, final, metadata)

    log.info(
        f"LLM translation: {len(to_translate)}/{len(texts)} texts "
        f"require API calls "
        f"(provider={cfg.provider}, model={cfg.model}, "
        f"context={'yes' if context else 'no'})."
    )

    for start in range(0, len(to_translate), chunk_size):
        chunk = to_translate[start : start + chunk_size]
        items = [t for _, t in chunk]

        try:
            payload = json.dumps({"items": items}, ensure_ascii=False)
            response = client.chat.completions.create(
                model=cfg.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload},
                ],
                max_tokens=settings.llm_max_tokens * 4,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        except Exception as exc:  # noqa: BLE001
            log.warning(
                f"LLM translation chunk failed "
                f"({start}-{start + len(chunk)}): {type(exc).__name__}: {exc}"
            )
            for i, _ in chunk:
                results[i] = ""
            continue

        if not response.choices:
            for i, _ in chunk:
                results[i] = ""
            continue

        raw = (response.choices[0].message.content or "").strip()
        raw = _strip_markdown_fences(raw)

        try:
            data = json.loads(raw)
            translated = data.get("translations", [])
        except (json.JSONDecodeError, AttributeError) as exc:
            log.warning(f"LLM translation returned invalid JSON: {exc}. " f"Raw: {raw[:200]}")
            translated = []

        if not isinstance(translated, list) or len(translated) != len(chunk):
            log.warning(
                f"LLM translation returned "
                f"{len(translated) if isinstance(translated, list) else '?'} "
                f"items for {len(chunk)} inputs."
            )
            if isinstance(translated, list):
                for (i, original), tr in zip(chunk, translated):
                    if isinstance(tr, str) and tr.strip():
                        cleaned = tr.strip()
                        results[i] = cleaned
                        cache_payload = f"{context or ''}|{original}" if context else original
                        _cache_set(
                            _CACHE_NS_TRA,
                            cfg.provider,
                            cfg.model,
                            cache_payload,
                            cleaned,
                        )
                    else:
                        results[i] = ""
            else:
                for i, _ in chunk:
                    results[i] = ""
            continue

        for (i, original), tr in zip(chunk, translated):
            if isinstance(tr, str) and tr.strip():
                cleaned = tr.strip()
                results[i] = cleaned
                cache_payload = f"{context or ''}|{original}" if context else original
                _cache_set(
                    _CACHE_NS_TRA,
                    cfg.provider,
                    cfg.model,
                    cache_payload,
                    cleaned,
                )
            else:
                results[i] = ""

    final = [r if r is not None else "" for r in results]
    return _apply_required_translations(texts, final, metadata)
