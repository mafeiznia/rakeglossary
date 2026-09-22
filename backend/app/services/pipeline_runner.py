"""Run the glossary pipeline in a background thread.

Orchestration depends on `project.processing_mode`:

    offline — classic definitions (in-text/Wiki/WordNet) + Google translation
    hybrid  — classic definitions + LLM translation (batch, context-aware)
    ai      — LLM extraction + LLM translation (single unified prompt,
              chunk-based, with full AI extras: pos, category, alternatives, notes)
"""

from __future__ import annotations

import math
import threading

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.project import ProcessingMode, Project
from app.models.project_source import ProjectSource, SourceType
from app.pipeline import llm_client
from app.pipeline.definitions import DefinitionSource, resolve_classic
from app.pipeline.extractors import load_text_from_source
from app.pipeline.glossary import (
    CancelledError,
    GlossaryEntry,
    _count_frequency,
    _find_context,
)
from app.pipeline.nlp import Keyword, extract_keywords
from app.pipeline.translation import translate_many
from app.services import (
    glossary_service,
    project_service,
    source_service,
)
from app.services.progress import ProgressEvent, tracker

log = get_logger("services.runner")


# ---------------------------------------------------------------------------
# Chunking config
# ---------------------------------------------------------------------------

# Words per chunk for AI extraction. Tuned so that:
#   - chunk fits comfortably in LLM context
#   - target term count per chunk stays reasonable (~50-80)
CHUNK_WORDS = 2500


def _split_into_chunks(text: str, chunk_words: int) -> list[str]:
    """Split `text` into word-based chunks, preserving word boundaries."""
    if not text or not text.strip():
        return []
    words = text.split()
    if len(words) <= chunk_words:
        return [text]
    chunks: list[str] = []
    for i in range(0, len(words), chunk_words):
        chunks.append(" ".join(words[i : i + chunk_words]))
    return chunks


# ---------------------------------------------------------------------------
# Cancellation registry
# ---------------------------------------------------------------------------

_CANCEL_FLAGS: dict[str, threading.Event] = {}
_FLAGS_LOCK = threading.Lock()


def _register_cancel_flag(project_id: str) -> threading.Event:
    ev = threading.Event()
    with _FLAGS_LOCK:
        _CANCEL_FLAGS[project_id] = ev
    return ev


def _pop_cancel_flag(project_id: str) -> None:
    with _FLAGS_LOCK:
        _CANCEL_FLAGS.pop(project_id, None)


def cancel_pipeline(project_id: str) -> bool:
    with _FLAGS_LOCK:
        ev = _CANCEL_FLAGS.get(project_id)
    if ev is None:
        return False
    ev.set()
    log.info(f"Cancellation requested for project {project_id[:8]}")
    return True


def is_running(project_id: str) -> bool:
    with _FLAGS_LOCK:
        return project_id in _CANCEL_FLAGS


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_source_text(source: ProjectSource) -> str:
    if source.source_type is SourceType.FILE and source.path:
        return load_text_from_source(file_path=source.path)
    return source.text_content or ""


def _per_source_num_terms(word_count: int, rate: float) -> int:
    return max(1, math.ceil(word_count * rate / 1000.0))


def _merge_classic_keywords(
    per_source: list[tuple[str, list[Keyword]]],
) -> list[tuple[str, float, list[str]]]:
    merged: dict[str, dict] = {}
    for source_name, kws in per_source:
        for kw in kws:
            key = kw.term.lower().strip()
            if key in merged:
                merged[key]["score"] += kw.score
                if source_name not in merged[key]["sources"]:
                    merged[key]["sources"].append(source_name)
            else:
                merged[key] = {
                    "term": kw.term,
                    "score": kw.score,
                    "sources": [source_name],
                }

    sorted_items = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return [(it["term"], it["score"], it["sources"]) for it in sorted_items]


def _load_included_sources(session: Session, project: Project) -> list[ProjectSource]:
    sources = [s for s in source_service.list_for_project(session, project.id) if s.included]
    return sources


# ---------------------------------------------------------------------------
# OFFLINE / HYBRID path (classic NLP + classic/LLM translation)
# ---------------------------------------------------------------------------


def _run_pipeline_classic(
    session: Session,
    project: Project,
    on_progress,
    cancel_event: threading.Event,
) -> list[GlossaryEntry]:
    """Classic extraction + classic definitions + mode-based translation."""
    mode = project.processing_mode

    sources = _load_included_sources(session, project)
    if not sources:
        raise RuntimeError("No usable source text found. Add at least one source.")
    total_sources = len(sources)

    metadata = project_service.get_book_metadata(project)

    from app.services import settings_service

    user_stop = settings_service.get_user_stopwords(session)

    # --- Extract keywords per source with buffer ---
    per_source_keywords: list[tuple[str, list[Keyword]]] = []
    full_text_parts: list[str] = []

    for i, src in enumerate(sources, start=1):
        if cancel_event.is_set():
            raise CancelledError("Cancelled during source loading.")

        text = _load_source_text(src)
        full_text_parts.append(f"--- Source: {src.original_name} ---\n\n{text.strip()}")

        n_target = _per_source_num_terms(src.word_count, project.terms_per_1k_words)
        n_extract = max(n_target * 3, n_target + 30)

        on_progress(
            f"Extracting up to {n_target} keywords (buffer={n_extract}) "
            f"from '{src.original_name}' ({src.word_count} words)",
            step="keywords",
            current=i,
            total=total_sources,
        )
        kws = extract_keywords(
            text,
            top_n=n_extract,
            use_spacy=project.use_spacy,
            use_rake=project.use_rake,
            use_yake=project.use_yake,
            use_ner=project.use_ner,
            extra_stopwords=frozenset(user_stop),
        )
        log.info(
            f"Source '{src.original_name}': "
            f"requested={n_extract}, got={len(kws)} (target={n_target})"
        )
        per_source_keywords.append((src.original_name, kws))

    # --- Merge + adaptive cap ---
    merged = _merge_classic_keywords(per_source_keywords)
    full_corpus = "\n\n".join(full_text_parts)
    total_words = len(full_corpus.split())
    log.info(
        f"Merged candidates (before cap): {len(merged)} terms, " f"corpus={total_words} words."
    )

    # Target: based on density (terms per 1000 words) but never above
    # the user-set num_terms cap.
    density_target = _per_source_num_terms(total_words, project.terms_per_1k_words)
    target = min(density_target, project.num_terms)

    log.info(
        f"Classic mode cap: density_target={density_target} "
        f"(density={project.terms_per_1k_words}/1k words), "
        f"num_terms={project.num_terms} → final target={target}"
    )

    if len(merged) > target:
        merged = merged[:target]

    log.info(f"Final term list: {len(merged)} terms (target={target}).")
    on_progress(
        f"Merged to {len(merged)} unique terms.",
        step="merge",
        current=1,
        total=1,
    )

    if not merged:
        raise RuntimeError("No keywords could be extracted from the source text.")

    # --- Resolve definitions ---
    term_data: list[dict] = []
    total_def = len(merged)
    for i, (term, score, _) in enumerate(merged, start=1):
        if cancel_event.is_set():
            raise CancelledError("Cancelled during definition resolution.")
        on_progress(
            f"Resolving definition {i}/{total_def}: '{term}'",
            step="definitions",
            current=i,
            total=total_def,
        )
        result = resolve_classic(term, full_corpus)
        term_data.append(
            {
                "term": term,
                "score": score,
                "definition": result.text,
                "source": result.source.value,
                "def_source": result.source,
            }
        )

    # --- Translate terms ---
    terms_to_translate = [d["term"] for d in term_data]
    persian_terms: list[str] = [""] * len(term_data)
    if project.translate_terms and terms_to_translate:
        if mode == ProcessingMode.OFFLINE:
            on_progress(
                f"Translating {len(terms_to_translate)} terms with Google...",
                step="translate",
                current=1,
                total=1,
            )
            try:
                persian_terms = translate_many(terms_to_translate, provider="google")
            except CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(f"Google term translation failed: {exc}")
        else:  # HYBRID
            on_progress(
                f"Translating {len(terms_to_translate)} terms with LLM...",
                step="translate",
                current=1,
                total=1,
            )
            try:
                persian_terms = llm_client.translate_many(
                    terms_to_translate,
                    metadata=metadata,
                )
            except CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(f"LLM term translation failed: {exc}")

    # --- Translate definitions ---
    def_idx = [
        i
        for i, d in enumerate(term_data)
        if d["def_source"] is not DefinitionSource.NONE
        and d["definition"]
        and d["definition"].strip()
    ]
    def_texts = [term_data[i]["definition"] for i in def_idx]

    persian_defs_full: list[str] = [""] * len(term_data)
    if project.translate_definitions and def_texts:
        if mode == ProcessingMode.OFFLINE:
            on_progress(
                f"Translating {len(def_texts)} definitions with Google...",
                step="translate",
                current=1,
                total=1,
            )
            try:
                translated = translate_many(def_texts, provider="google")
                for i, tr in zip(def_idx, translated):
                    persian_defs_full[i] = tr
            except CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(f"Google definition translation failed: {exc}")
        else:  # HYBRID
            on_progress(
                f"Translating {len(def_texts)} definitions with LLM...",
                step="translate",
                current=1,
                total=1,
            )
            try:
                translated = llm_client.translate_many(
                    def_texts,
                    metadata=metadata,
                )
                for i, tr in zip(def_idx, translated):
                    persian_defs_full[i] = tr
            except CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(f"LLM definition translation failed: {exc}")

    # --- Assemble entries ---
    entries: list[GlossaryEntry] = []
    total = len(term_data)
    for i, d in enumerate(term_data, start=1):
        if cancel_event.is_set():
            raise CancelledError("Cancelled during finalization.")
        on_progress(
            f"[{i}/{total}] Finalizing '{d['term']}'",
            step="process",
            current=i,
            total=total,
        )
        entries.append(
            GlossaryEntry(
                english_term=d["term"],
                persian_term=persian_terms[i - 1],
                english_definition=d["definition"],
                persian_definition=persian_defs_full[i - 1],
                source=d["source"],
                score=round(d["score"], 4),
                frequency=_count_frequency(d["term"], full_corpus),
                context=_find_context(d["term"], full_corpus, 200),
            )
        )

    return entries


# ---------------------------------------------------------------------------
# AI path (LLM extraction + translation, chunk-based)
# ---------------------------------------------------------------------------


def _run_pipeline_ai(
    session: Session,
    project: Project,
    on_progress,
    cancel_event: threading.Event,
) -> list[GlossaryEntry]:
    """AI Mode: LLM extracts terms + Persian translations + all extras.

    Text is split into word-based chunks; each chunk goes through one LLM
    call that returns structured items with: term, persian_term,
    persian_alternatives, context, pos, category, translator_note,
    persian_transliteration.
    """
    sources = _load_included_sources(session, project)
    if not sources:
        raise RuntimeError("No usable source text found. Add at least one source.")

    metadata = project_service.get_book_metadata(project)
    if metadata:
        log.info("AI mode: using book metadata for prompt.")
    else:
        log.info("AI mode: no book metadata; using default prompt.")

    # --- Build the list of (source, chunk) work units ---
    work_units: list[tuple[str, str, int]] = []  # (source_name, chunk_text, chunk_index)
    full_text_parts: list[str] = []

    for src in sources:
        if cancel_event.is_set():
            raise CancelledError("Cancelled during source loading.")
        text = _load_source_text(src)
        full_text_parts.append(f"--- Source: {src.original_name} ---\n\n{text.strip()}")
        chunks = _split_into_chunks(text, CHUNK_WORDS)
        for j, chunk in enumerate(chunks, start=1):
            work_units.append((src.original_name, chunk, j))

    total_units = len(work_units)
    log.info(f"AI mode: {total_units} chunk(s) across {len(sources)} source(s).")

    if total_units == 0:
        raise RuntimeError("No content to process.")

    # --- Extract from each chunk ---
    all_terms: dict[str, dict] = {}  # key = lower(term)
    for idx, (source_name, chunk_text, chunk_idx) in enumerate(work_units, start=1):
        if cancel_event.is_set():
            raise CancelledError("Cancelled during extraction.")

        chunk_words = len(chunk_text.split())
        # Target for this chunk based on its own word count
        chunk_target = _per_source_num_terms(chunk_words, project.terms_per_1k_words)
        # Minimum threshold and hard cap
        chunk_target = max(3, min(chunk_target, 200))

        on_progress(
            f"LLM extracting ~{chunk_target} terms from chunk "
            f"{chunk_idx} of '{source_name}' ({chunk_words} words) "
            f"[{idx}/{total_units}]",
            step="keywords",
            current=idx,
            total=total_units,
        )

        chunk_id = f"{source_name}#{chunk_idx}"
        try:
            extracted = llm_client.extract_terms_llm(
                chunk_text,
                metadata,
                target_count=chunk_target,
                chunk_id=chunk_id,
            )
        except CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning(f"LLM extraction failed for {chunk_id}: " f"{type(exc).__name__}: {exc}")
            extracted = []

        log.info(f"Chunk {chunk_id}: {len(extracted)} terms " f"(target={chunk_target})")

        for item in extracted:
            key = item["term"].lower().strip()
            if not key:
                continue
            if key not in all_terms:
                all_terms[key] = item

    # --- Merge + adaptive cap ---
    merged_terms = list(all_terms.values())
    log.info(f"AI mode: merged {len(merged_terms)} unique terms.")

    full_corpus = "\n\n".join(full_text_parts)
    total_words = len(full_corpus.split())

    # Same density-based target as classic mode
    density_target = _per_source_num_terms(total_words, project.terms_per_1k_words)
    target = min(density_target, project.num_terms)

    log.info(
        f"AI mode cap: density_target={density_target}, "
        f"num_terms={project.num_terms} → final target={target}"
    )

    if len(merged_terms) > target:
        log.info(f"AI mode: capping {len(merged_terms)} terms at target={target}.")
        merged_terms.sort(
            key=lambda t: _count_frequency(t["term"], full_corpus),
            reverse=True,
        )
        merged_terms = merged_terms[:target]

    if not merged_terms:
        raise RuntimeError("LLM could not extract any terms. " "Check API key and try again.")

    # --- Assemble entries (translation is already in extracted items) ---
    entries: list[GlossaryEntry] = []
    total = len(merged_terms)
    with_pos = 0
    with_note = 0
    with_context = 0

    for i, t in enumerate(merged_terms, start=1):
        if cancel_event.is_set():
            raise CancelledError("Cancelled during finalization.")
        on_progress(
            f"[{i}/{total}] Finalizing '{t['term']}'",
            step="process",
            current=i,
            total=total,
        )

        freq = _count_frequency(t["term"], full_corpus)
        score = min(1.0, freq / 10.0) if freq > 0 else 0.1

        ctx = (t.get("context") or "").strip()
        if not ctx:
            ctx = _find_context(t["term"], full_corpus, 200)
        if ctx:
            with_context += 1

        pos = t.get("pos")
        category = t.get("category")
        alternatives = t.get("persian_alternatives") or []
        note = t.get("translator_note")
        transliteration = t.get("persian_transliteration")

        if pos:
            with_pos += 1
        if note:
            with_note += 1

        entries.append(
            GlossaryEntry(
                english_term=t["term"],
                persian_term=t.get("persian_term") or "",
                english_definition="",
                persian_definition="",
                source="LLM",
                score=round(score, 4),
                frequency=freq,
                context=ctx,
                pos=pos,
                category=category,
                persian_alternatives=alternatives if alternatives else None,
                translator_note=note,
                persian_transliteration=transliteration,
            )
        )

    log.info(
        f"AI mode: {len(entries)} entries "
        f"(context={with_context}, pos={with_pos}, note={with_note})."
    )

    return entries


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def _run_pipeline_sync(project_id: str, session: Session | None = None) -> None:
    own_session = session is None
    if own_session:
        session = SessionLocal()

    assert session is not None

    cancel_event = _register_cancel_flag(project_id)

    try:
        project = session.get(Project, project_id)
        if project is None:
            log.error(f"Pipeline requested for unknown project {project_id}")
            return

        mode = project.processing_mode

        if mode in (ProcessingMode.AI, ProcessingMode.HYBRID) and not llm_client.is_configured():
            raise RuntimeError(
                f"Processing mode is '{mode.value}' but no LLM provider " f"is configured."
            )

        tracker.create(project_id)
        project_service.mark_processing(session, project)
        tracker.publish(
            ProgressEvent(
                project_id=project_id,
                level="info",
                message=f"Started (mode={mode.value})",
                step="start",
            )
        )

        def on_progress(message: str, step: str = "", current: int = 0, total: int = 0) -> None:
            tracker.publish(
                ProgressEvent(
                    project_id=project_id,
                    message=message,
                    step=step,
                    current=current,
                    total=total,
                )
            )

        if mode == ProcessingMode.AI:
            entries = _run_pipeline_ai(
                session,
                project,
                on_progress,
                cancel_event,
            )
        else:
            entries = _run_pipeline_classic(
                session,
                project,
                on_progress,
                cancel_event,
            )

        glossary_service.replace_entries(session, project_id, entries)
        project_service.mark_done(session, project)

        tracker.publish(
            ProgressEvent(
                project_id=project_id,
                level="success",
                message=f"Finished: {len(entries)} entries",
                step="done",
                current=len(entries),
                total=len(entries),
            )
        )

    except CancelledError as exc:
        log.info(f"Pipeline cancelled for project {project_id[:8]}")
        try:
            project = session.get(Project, project_id)
            if project is not None:
                project_service.mark_cancelled(session, project, str(exc))
        except Exception:
            log.exception("Failed to mark project as cancelled.")
        tracker.publish(
            ProgressEvent(
                project_id=project_id,
                level="warning",
                message="Cancelled by user",
                step="cancelled",
            )
        )

    except Exception as exc:
        log.exception(f"Pipeline failed for project {project_id}")
        try:
            project = session.get(Project, project_id)
            if project is not None:
                project_service.mark_failed(session, project, str(exc))
        except Exception:
            log.exception("Failed to mark project as failed.")
        tracker.publish(
            ProgressEvent(
                project_id=project_id,
                level="error",
                message=f"Error: {exc}",
                step="error",
            )
        )

    finally:
        tracker.close(project_id)
        _pop_cancel_flag(project_id)
        if own_session:
            session.close()


def start_pipeline(project_id: str) -> threading.Thread:
    log.info(f"Starting pipeline for project {project_id[:8]}")
    t = threading.Thread(
        target=_run_pipeline_sync,
        args=(project_id,),
        name=f"pipeline-{project_id[:8]}",
        daemon=True,
    )
    t.start()
    return t
