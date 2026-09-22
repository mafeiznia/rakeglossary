"""High-level glossary generation orchestrator."""

from __future__ import annotations

import re
import threading


class CancelledError(Exception):
    """Raised when the pipeline is cancelled by the user."""


from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from app.core.logging import get_logger
from app.pipeline.definitions import DefinitionSource, resolve
from app.pipeline.extractors import load_text_from_source
from app.pipeline.nlp import Keyword, extract_keywords
from app.pipeline.translation import translate

log = get_logger("pipeline.glossary")

ProgressCallback = Callable[[str, str, int, int], None] | None


@dataclass
class GlossaryEntry:
    """A single glossary row."""

    english_term: str
    persian_term: str
    english_definition: str
    persian_definition: str
    source: str
    score: float
    frequency: int
    context: str
    # --- AI Mode extras (optional, None in Offline/Hybrid) ---
    pos: str | None = None
    category: str | None = None
    persian_alternatives: list[str] | None = None
    translator_note: str | None = None
    persian_transliteration: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GlossaryOptions:
    """Runtime options controlling the pipeline."""

    num_terms: int = 500
    terms_per_1k_words: float = 15.0
    translate_terms: bool = True
    translate_definitions: bool = True
    translation_provider: str = "google"
    use_spacy: bool = True
    use_rake: bool = True
    use_yake: bool = True
    use_ner: bool = True
    context_window: int = 200
    extra_stopwords: frozenset[str] = field(default_factory=frozenset)


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_BOUNDARY_TEMPLATE = r"\b{}\b"


def _find_context(term: str, text: str, window: int) -> str:
    if not term:
        return ""
    pattern = _WORD_BOUNDARY_TEMPLATE.format(re.escape(term))
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""

    start = match.start()
    sent_start = start
    for m in _SENTENCE_SPLIT_RE.finditer(text[:start]):
        sent_start = m.end()
    tail = text[match.end() :]
    sent_end_match = _SENTENCE_SPLIT_RE.search(tail)
    sent_end = match.end() + (sent_end_match.start() if sent_end_match else len(tail))

    snippet = text[sent_start:sent_end].strip()
    if len(snippet) > window:
        snippet = snippet[:window].rstrip() + "..."
    return snippet


def _count_frequency(term: str, text: str) -> int:
    if not term:
        return 0
    pattern = _WORD_BOUNDARY_TEMPLATE.format(re.escape(term))
    return len(re.findall(pattern, text, re.IGNORECASE))


def generate_glossary(
    file_path: str | None = None,
    raw_text: str | None = None,
    options: GlossaryOptions | None = None,
    on_progress: ProgressCallback = None,
    cancel_event: threading.Event | None = None,
) -> list[GlossaryEntry]:
    """Run the full glossary generation pipeline.

    Args:
        file_path: Path to a supported document, or None.
        raw_text: Direct text input, or None.
        options: Pipeline options.
        on_progress: Optional callback `(message, step, current, total)`.
        cancel_event: If set, the pipeline checks this between each keyword
            and raises `CancelledError` as soon as it is signalled.

    Raises:
        CancelledError: If `cancel_event` becomes set during processing.
    """
    opts = options or GlossaryOptions()

    def emit(message: str, step: str = "", current: int = 0, total: int = 0) -> None:
        if on_progress is not None:
            on_progress(message, step, current, total)

    def check_cancel() -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError("Pipeline cancelled by user.")

    # --- Step 1: load text ---
    emit("Loading input text...", step="load")
    text = load_text_from_source(file_path=file_path, raw_text=raw_text)
    if not text or not text.strip():
        log.error("Pipeline aborted: empty text buffer.")
        emit("Aborted: empty text", step="load")
        return []

    log.info(f"Text ready: {len(text.split())} words.")
    emit(f"Loaded {len(text.split())} words", step="load", current=1, total=1)
    check_cancel()

    # --- Step 2: extract keywords ---
    emit("Extracting keywords...", step="keywords")
    keywords: list[Keyword] = extract_keywords(
        text,
        top_n=opts.num_terms,
        use_spacy=opts.use_spacy,
        use_rake=opts.use_rake,
        use_yake=opts.use_yake,
        use_ner=opts.use_ner,
        extra_stopwords=opts.extra_stopwords,
    )
    if not keywords:
        log.warning("No keywords extracted; returning empty glossary.")
        emit("No keywords extracted", step="keywords")
        return []

    log.info(f"Extracted {len(keywords)} keywords.")
    emit(f"Extracted {len(keywords)} keywords", step="keywords", current=1, total=1)
    check_cancel()

    # --- Step 3: resolve definitions and translate ---
    entries: list[GlossaryEntry] = []
    total = len(keywords)
    for i, kw in enumerate(keywords, start=1):
        check_cancel()
        log.info(f"[{i}/{total}] Processing '{kw.term}' (score={kw.score:.3f})")
        emit(f"Processing '{kw.term}'", step="process", current=i, total=total)

        definition_result = resolve(kw.term, text)
        definition_text = definition_result.text
        source_name = definition_result.source.value

        persian_term = ""
        if opts.translate_terms:
            persian_term = translate(
                kw.term,
                provider=opts.translation_provider,
                source="en",
                target="fa",
            )

        persian_definition = ""
        if opts.translate_definitions and definition_result.source is not DefinitionSource.NONE:
            persian_definition = translate(
                definition_text,
                provider=opts.translation_provider,
                source="en",
                target="fa",
            )

        entries.append(
            GlossaryEntry(
                english_term=kw.term,
                persian_term=persian_term,
                english_definition=definition_text,
                persian_definition=persian_definition,
                source=source_name,
                score=round(kw.score, 4),
                frequency=_count_frequency(kw.term, text),
                context=_find_context(kw.term, text, opts.context_window),
            )
        )

    log.info(f"Glossary generation complete: {len(entries)} entries.")
    emit(f"Complete: {len(entries)} entries", step="done", current=total, total=total)
    return entries
