# Changelog

All notable changes to RakeGlossary are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- Windows packaging (`.exe` + installer)
- LLM reflection for glossary refinement
- Translation memory across projects
- Folder linking (scan a folder instead of uploading files)
- Additional target languages
- Alembic migrations
- Frontend tests (Vitest)

---

## [0.1.0] — 2026-09-21

First working version of RakeGlossary. Local-first desktop glossary generator with three processing modes, multi-source projects, book metadata support, and a fully themable bilingual UI.

### Added

#### Core Pipeline

- **Multi-format text extraction:**
  - PDF via PyMuPDF (no OCR)
  - DOCX via python-docx (paragraphs + tables)
  - EPUB via ebooklib + BeautifulSoup (noise-stripped)
  - TXT with auto encoding detection
- **NLP keyword extraction:**
  - spaCy noun chunks (with POS filtering)
  - spaCy NER (PERSON, GPE, LOC, ORG, PRODUCT, EVENT, ...)
  - RAKE (co-occurrence based)
  - YAKE (statistical, unsupervised)
  - Combined scoring with per-source weights + consensus bonus
- **Definition resolution (layered):**
  - In-text pattern matching
  - Wikipedia REST Summary API (with disambiguation detection)
  - WordNet (offline, NLTK)
  - LLM (in AI mode)
- **Translation:**
  - Google Translate (online, via deep-translator)
  - LibreTranslate (self-hosted)
  - Argos Translate (fully offline, ARM64-friendly)
  - LLM (context-aware, batch, with book metadata)
- **Three processing modes:**
  - **Offline** — Classic NLP + Wikipedia/WordNet + Argos
  - **Hybrid** — Classic NLP + Wikipedia/WordNet + LLM translation
  - **AI** — LLM extraction + LLM translation (unified prompt)

#### AI Mode Enhancements

- Chunk-based extraction (`CHUNK_WORDS = 2500`)
- Rich extraction prompt (editor + terminologist role)
- Per-chunk target derived from word count and density
- AI extras stored per entry:
  - `pos` (Part of Speech)
  - `category` (Domain Jargon / Character Name / ...)
  - `persian_alternatives` (up to 3 synonyms)
  - `translator_note`
  - `persian_transliteration`
- Context-aware translation using book metadata
- Zero-hallucination validation (every term must appear verbatim in source)
- Context validation (context must contain the term)
- Unicode normalization for curly quotes, dashes, non-breaking spaces

#### Projects & Sources

- **Multi-source projects:** add many files or text snippets to one project
- **Duplicate file detection** by SHA-256 hash
- **Alphabetical source ordering** with `order_index`
- **Toggle inclusion** per source (excluded sources are skipped)
- **Rename sources** from the UI
- **Per-project folder structure:** `data/projects/{title}__{id8}/`
- **Auto-rename folder** when project title changes
- **Aggregate caching:** `word_count` and `source_count` on the project

#### Book Metadata

- Manual form with 13 fields:
  - `title`, `original_title`, `author`
  - `primary_genre`, `sub_genres`, `main_themes`
  - `time_period`, `location`
  - `target_audience`, `reading_level`, `vocabulary_complexity`
  - `cultural_context`, `key_terminology`
- JSON upload alternative (BookSpecsTemplate.json)
- Mutual exclusion between manual and JSON (persisted via `metadata_source`)
- **English-only validation** on text fields
- **Key terminology** with `term=translation` format (no spaces, Enter-separated)
- Tooltips and help text on every field

#### Glossary Editing

- Inline editing with Enter to save, Esc to cancel
- Add to global blacklist (🚫)
- Delete entry from current project (🗑️)
- Context column showing source sentence
- Tooltips on Source values (In-Text / Wikipedia / WordNet / LLM / None)
- Editable Persian term and definition

#### Settings

- **Global user stopwords (blacklist):** applied across all projects
- English-only validation on blacklist input
- **LLM configuration:**
  - 7 providers: OpenAI, OpenRouter, Gemini, GapGPT, DeepSeek, Groq, Custom
  - API key storage (plaintext in local SQLite)
  - Model selection with suggestions
  - Test connection with latency measurement
  - Auto-clear key when provider changes
- **Appearance:**
  - 5 themes: Indigo Light, Emerald Light, Rose Light, Slate Dark, Midnight Dark
  - Theme applied before React mounts (no FOUC)
- **Language:** Persian (RTL) / English (LTR)
- **Back to last project** button

#### Export

- **CSV:** compact 2-column (English Term, Persian Term), UTF-8-SIG for Excel
- **XLSX:** full 13-column table with RTL alignment for Persian columns
- **TBX:** ISO 30042 TermBase eXchange for CAT tools

#### Progress & Cancellation

- **Server-Sent Events (SSE)** stream for live progress
- **Progress tracker** with 100-event history for late subscribers
- **Per-event fields:** message, step, current, total, level, timestamp
- **Cooperative cancellation** via `threading.Event` per project
- **Stop button** in UI with confirmation dialog
- Auto-scroll to bottom (only inside the log container)
- Keep-alive every 15s to avoid proxy timeouts

#### User Interface

- **Toast notifications** via Sonner (replacing native `alert` / `confirm`)
- **ConfirmDialog** via Radix UI with Promise-based `useConfirm()`
- **Empty States** with icon + title + description + action button
- **Loading skeletons** with shimmer effect
- **Tooltips** via Radix UI with 300ms delay
- **Animations:**
  - Route transitions (fade)
  - Panel expand/collapse
  - Dialog scale + fade (250ms)
  - Progress log events (stagger)
  - Button hover + active scale
  - Table rows (fade-in)
  - Empty state stagger
- **RTL / LTR** support with logical Tailwind properties
- **Theming** via CSS custom properties

#### Developer Experience

- **Windows batch scripts:**
  - `setup.bat` — one-time setup
  - `dev.bat` — run both servers
  - `dev-backend.bat` / `dev-frontend.bat` — individual servers
  - `cmd.bat` — interactive shell with venv
- **Port conflict detection** before starting
- **Path normalization** for project root resolution
- **Pytest suite:** ~200 tests covering extractors, NLP, definitions, translation, schemas, DB, services, and API endpoints
- **Loguru** logging with rotation (10 MB, 14 days) and UTF-8

### Changed

- Storage layout moved from `data/uploads/{project_id}/` to `data/projects/{title}__{id8}/`
- CSV export reduced from 13 columns to 2 (XLSX and TBX keep the full set)
- Hybrid mode term cap now respects `min(density_target, num_terms)`
- LLM extraction uses chunking instead of hard truncation at 60k characters
- `_source` metadata marker renamed to `metadata_source` and persisted
- `cancelled` status now uses `XCircle` icon (was `AlertCircle`)
- `--color-warning` in light themes changed from amber-600 to amber-500 for better clarity

### Fixed

- **Circular import** in `services/__init__.py` (`__getattr__` with `importlib`)
- **`ProjectRead.book_metadata` Pydantic validation** when DB stores it as a string
- **`ProjectRead.processing_mode`** now accepts both Enum and string from ORM
- **Frequency filter** in classic mode no longer drops all terms for short texts
- **`t is not defined`** in `_run_pipeline_classic` entries assembly
- **`optionsRef is not defined`** in OptionsPanel after incomplete replacement
- **Stop button** now shows a proper confirmation dialog
- **Blacklist button** works with the global confirm system
- **Delete entry button** works with the global confirm system
- **Cancel toast** now says "Processing stopped" (was "Saved")
- **Wikipedia disambiguation pages** no longer appear as definitions
- **Duplicated Argos translations** for short inputs are collapsed
- **PDF warnings** from deprecated `fitz` import are gone (using `pymupdf`)
- **SSE events are no longer lost** when the page is refreshed mid-pipeline

### Security

- File extension allowlist: `.pdf`, `.docx`, `.epub`, `.txt`
- Max file size: 200 MB
- Filename sanitization prevents path traversal
- UUID prefixes prevent filename collisions
- Localhost-only binding (`127.0.0.1`)
- CORS restricted to development origins only

### Known Limitations

- No OCR support for scanned PDFs
- No folder linking (files must be uploaded)
- English-only source input (NLP pipeline)
- No translation memory across projects
- No Alembic migrations (delete DB to change schema)
- AI mode does not translate definitions (cost optimization)
- Progress events are in-memory only (lost on backend restart)
- Wikipedia lookups are serial (not parallelized)
- Score in AI mode is derived from frequency (LLM doesn't provide scores)

---

## Release Notes Format

For future releases, entries should be grouped under:

- **Added** — new features
- **Changed** — changes to existing behavior
- **Deprecated** — features that will be removed
- **Removed** — features that were removed
- **Fixed** — bug fixes
- **Security** — security-related changes

---

## Version History

| Version | Date | Highlights |
|---|---|---|
| **0.1.0** | 2026-09-21 | First working release: 3 modes, 7 LLM providers, 3 translation providers, 5 themes, ~200 tests |