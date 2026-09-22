# Architecture

> Technical architecture and design decisions for RakeGlossary

## Table of Contents

- [Overview](#-overview)
- [High-Level Architecture](#-high-level-architecture)
- [Backend Architecture](#-backend-architecture)
- [Frontend Architecture](#-frontend-architecture)
- [Data Model](#-data-model)
- [Data Flow](#-data-flow)
- [Pipeline Modes](#-pipeline-modes)
- [Key Design Decisions](#-key-design-decisions)
- [Security & Privacy](#-security--privacy)
- [Performance Considerations](#-performance-considerations)
- [Extension Points](#-extension-points)
- [Known Limitations](#-known-limitations)

---

## 🎯 Overview

RakeGlossary is a **local-first desktop application** that generates bilingual (EN → FA) glossaries from books and documents.

**Core principles:**

1. **Local-first** — all data stays on the user's machine. Only LLM/translation calls go out (and only when the user opts in).
2. **Pluggable** — pipeline components (extractors, NLP, definitions, translation, LLM) are swappable.
3. **Observable** — every stage emits progress events consumed by the UI via SSE.
4. **Crash-safe** — long-running pipelines run in background threads; the UI can reconnect.

---

## 🏗 High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Windows Desktop                       │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  pywebview window (future)                         │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  React SPA (Vite build, served locally)      │  │  │
│  │  │  - Tailwind CSS + Radix UI                   │  │  │
│  │  │  - Zustand + TanStack Query                  │  │  │
│  │  │  - i18next (fa/en) + RTL support             │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                          │ HTTP + SSE                     │
│                          ▼                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  FastAPI (Uvicorn, 127.0.0.1:8765)                 │  │
│  │  - REST endpoints                                  │  │
│  │  - SSE progress stream                             │  │
│  │  - Static export download                          │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                                │
│                          ▼                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Pipeline Orchestrator (background thread)         │  │
│  │  ┌──────────┬──────────┬────────────┬───────────┐  │  │
│  │  │Extractors│   NLP    │ Definitions│Translation│  │  │
│  │  └──────────┴──────────┴────────────┴───────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                                │
│                          ▼                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  SQLite + file-based storage (data/)               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼ (optional, user-enabled)
                  ┌───────────────────────────┐
                  │  External APIs            │
                  │  - Wikipedia (REST)       │
                  │  - LLM providers          │
                  │  - Translation providers  │
                  └───────────────────────────┘
```

---

## 🐍 Backend Architecture

### Package Layout

```
backend/app/
├── api/                # FastAPI routers (thin HTTP layer)
│   ├── projects.py
│   ├── sources.py
│   ├── glossary.py
│   ├── process.py
│   ├── export.py
│   └── settings.py
│
├── core/               # Cross-cutting concerns
│   ├── config.py       # Settings + Paths (env-overridable)
│   ├── db.py           # SQLAlchemy engine + Base
│   ├── logging.py      # loguru configuration
│   └── version.py
│
├── models/             # SQLAlchemy ORM models
│   ├── project.py
│   ├── project_source.py
│   ├── glossary_entry.py
│   └── setting.py
│
├── schemas/            # Pydantic v2 schemas (I/O contracts)
│   ├── project.py
│   ├── source.py
│   ├── glossary.py
│   └── settings.py
│
├── services/           # Business logic
│   ├── project_service.py
│   ├── source_service.py
│   ├── glossary_service.py
│   ├── export_service.py
│   ├── settings_service.py
│   ├── llm_config_service.py
│   ├── storage.py      # File uploads
│   ├── progress.py     # In-memory tracker for SSE
│   └── pipeline_runner.py
│
└── pipeline/           # Glossary generation pipeline
    ├── extractors/     # Document → text
    ├── nlp/            # Text → candidate keywords
    ├── definitions/    # Keyword → definition
    ├── translation/    # Text → Persian
    ├── glossary.py     # Core orchestrator
    └── llm_client.py   # Unified LLM interface
```

### Layering Rules

1. **api/** depends on **services/** and **schemas/**
2. **services/** depends on **models/**, **schemas/**, **pipeline/**, **core/**
3. **pipeline/** depends on **core/** only (never on services)
4. **core/** depends on nothing internal

This keeps the pipeline testable in isolation and prevents circular imports.

### Key Components

**`services/progress.py` — `ProgressTracker`**

Thread-safe event bus used to bridge:
- **Producer:** pipeline running in a background thread
- **Consumer:** SSE endpoint running in asyncio event loop

Uses `queue.Queue` with a bounded history (last 100 events). Late subscribers replay history before receiving live events.

**`services/pipeline_runner.py`**

Spawns a daemon thread per project. Manages:
- Cancellation via a registry of `threading.Event` per project
- Progress emission
- Final state transitions (done / failed / cancelled)

**`pipeline/llm_client.py`**

Single entry point for all LLM operations. Encapsulates:
- Provider selection (from `llm_providers.json`)
- Rate limiting? (No — LLM providers handle their own rate limits; we only retry on errors)
- Caching of definitions and translations via diskcache
- Prompt construction with book metadata

---

## ⚛️ Frontend Architecture

### Package Layout

```
frontend/src/
├── api/                # HTTP client + typed endpoints
│   ├── client.ts       # Axios instance + error interceptor
│   ├── projects.ts
│   ├── sources.ts
│   ├── glossary.ts
│   ├── process.ts
│   ├── export.ts
│   ├── settings.ts
│   └── llm.ts
│
├── components/         # Reusable UI components
│   ├── ui/             # Primitives (Button, Input, Dialog, ...)
│   └── layout/         # AppLayout, Header, Sidebar
│
├── features/           # Feature-scoped modules
│   ├── projects/       # Project cards, hooks, options
│   ├── sources/        # Multi-file upload, source list
│   ├── glossary/       # Table, editable cells
│   ├── progress/       # ProgressLog, useProgressStream
│   ├── metadata/       # BookMetadataPanel
│   ├── settings/       # LLM settings, Stopwords, theme
│   └── confirm/        # Global ConfirmDialog host
│
├── pages/              # Route-level components
│   ├── HomePage.tsx
│   ├── ProjectsPage.tsx
│   ├── ProjectDetailPage.tsx
│   └── SettingsPage.tsx
│
├── i18n/               # Translations
│   ├── index.ts
│   ├── fa.ts
│   └── en.ts
│
├── types/              # Shared TypeScript types
│   ├── project.ts
│   ├── source.ts
│   ├── glossary.ts
│   └── progress.ts
│
├── lib/                # Pure helpers
│   ├── utils.ts
│   └── queryClient.ts
│
├── App.tsx             # Router + Toaster + TooltipProvider
└── main.tsx
```

### State Management Strategy

| State type | Tool | Rationale |
|---|---|---|
| Server state | TanStack Query | Caching, invalidation, refetch |
| UI preferences | Zustand + persist | Theme, language (survives reload) |
| Transient UI | React useState | Local to component |
| Cross-component dialog | Zustand + Promise | `useConfirm()` returns a Promise |
| Progress events | Custom hook + EventSource | SSE streaming |

### Theming

Themes are implemented as **CSS custom properties** on `:root` with `data-theme` attribute:

```css
:root[data-theme="indigo-light"] {
  --color-primary: 79 70 229;
  --color-surface: 255 255 255;
  /* ... */
}
```

Format is `R G B` (space-separated) so opacity modifiers work:

```typescript
style={{ color: 'rgb(var(--color-primary) / 0.5)' }}
```

Theme is applied **before React mounts** via a small inline script in `index.html` to avoid FOUC.

---

## 🗄 Data Model

### Tables

**`projects`**

| Column | Type | Notes |
|---|---|---|
| id | UUID (str) | PK |
| order_seq | int | Monotonic counter for stable ordering |
| title | str | User-provided |
| status | enum | pending / processing / done / failed / cancelled |
| num_terms | int | User-set cap |
| terms_per_1k_words | float | Density setting |
| translate_terms | bool | |
| translate_definitions | bool | |
| translation_provider | str | |
| processing_mode | enum | offline / ai / hybrid |
| use_spacy / use_rake / use_yake / use_ner | bool | NLP flags |
| book_metadata | text (JSON) | Flexible metadata blob |
| word_count | int | Aggregate (cached) |
| source_count | int | Aggregate (cached) |
| created_at / updated_at / started_at / finished_at | datetime | |
| error_message | text | If failed |

**`project_sources`**

| Column | Type | Notes |
|---|---|---|
| id | int | PK, autoincrement |
| project_id | UUID (str) | FK → projects.id (CASCADE) |
| source_type | enum | file / text |
| path | str | For file sources |
| text_content | text | For text sources |
| original_name | str | Display name |
| file_hash | str | SHA-256 for dedup |
| word_count | int | |
| order_index | int | Alphabetical ordering |
| included | bool | Toggle inclusion |

**`glossary_entries`**

| Column | Type | Notes |
|---|---|---|
| id | int | PK |
| project_id | UUID (str) | FK → projects.id (CASCADE) |
| english_term | str | |
| persian_term | str | |
| english_definition | text | |
| persian_definition | text | |
| source | str | In-Text / Wikipedia / WordNet / LLM / None |
| score | float | |
| frequency | int | |
| context | text | Sentence from source |
| is_edited | bool | Manual edits |
| pos | str (nullable) | AI mode only |
| category | str (nullable) | AI mode only |
| persian_alternatives | text (JSON) | AI mode only |
| translator_note | text (nullable) | AI mode only |
| persian_transliteration | str (nullable) | AI mode only |

**`settings`** — key/value store. Values are JSON-encoded strings. Used for:
- `user_stopwords` — global blacklist
- `llm_config` — LLM provider config + API key

### Relationships

```
Project 1───N ProjectSource
Project 1───N GlossaryEntry
```

Both cascades delete when a project is deleted.

### File Storage

```
data/
├── rakeglossary.db           # SQLite
├── projects/
│   └── {sanitized_title}__{id8}/
│       ├── {uuid12}__{filename}  # Uploaded files
│       └── metadata.json         # (optional, for JSON imports)
├── exports/                  # Temporary export files
├── cache/
│   └── translations/         # diskcache for translation cache
└── logs/
    └── rakeglossary.log      # Rotating log
```

---

## 🔄 Data Flow

### Project Creation Flow

```
User fills form (title + sources + metadata)
        │
        ▼
POST /api/projects            → ProjectCreateEmpty
        │
        ├─► INSERT project
        ├─► mkdir data/projects/{title}__{id8}/
        └─► return ProjectRead
        │
        ▼
POST /api/projects/{id}/sources/upload   (multi-file)
        │
        ├─► for each file:
        │     ├─ compute SHA-256
        │   ├─ check duplicate in project
        │   ├─ save to disk
        │   ├─ extract text
        │   └─ INSERT project_source
        │
        └─► recompute_aggregates(project)
```

### Pipeline Execution Flow

```
POST /api/process/{id}         → ProcessRequest
        │
        ├─► apply_process_options(project)
        ├─► mark_processing(project)
        ├─► pipeline_runner.start_pipeline(id)  → background thread
        └─► return ProjectRead (status=processing)
        
        [background thread]
        │
        ├─► load sources (included only)
        ├─► dispatch by mode: AI / Hybrid / Offline
        ├─► emit progress events (via tracker)
        ├─► save GlossaryEntry rows
        ├─► mark_done / mark_failed / mark_cancelled
        └─► tracker.close(id)

        [SSE endpoint]
        GET /api/process/{id}/events
        │
        ├─► replay history
        ├─► subscribe to tracker queue
        └─► stream events until sentinel
```

---

## 🎛 Pipeline Modes

### Offline Mode

```
Text → NLP (spaCy + RAKE + YAKE + NER)
        │
        ▼
merge + dedup + cap by density
        │
        ▼
definitions: in-text → Wikipedia → WordNet
        │
        ▼
translation: Argos (offline, per-term)
```

### Hybrid Mode

```
Text → NLP (same as Offline)
        │
        ▼
merge + dedup + cap
        │
        ▼
definitions: in-text → Wikipedia → WordNet
        │
        ▼
translation: LLM (batch, context-aware)
```

### AI Mode

```
Text → split into chunks (~2500 words each)
        │
        ▼
for each chunk:
    LLM extracts terms + definitions + context
    with a specialized prompt (editor + terminologist)
        │
        ▼
merge + dedup + cap by density
        │
        ▼
translation: LLM (context-aware, batch)
        │
        ▼
no definitions are stored (by design)
```

---

## 🔑 Key Design Decisions

### 1. Local-first storage

**Decision:** Store everything in SQLite + local files, not a cloud.

**Rationale:** Privacy, offline capability, no infrastructure costs. Users' books never leave their machine except for optional LLM/translation calls.

### 2. Background thread for pipeline

**Decision:** Pipeline runs in a `threading.Thread`, not in asyncio.

**Rationale:** The pipeline is CPU-bound (NLP) and does blocking I/O (files, HTTP). Running it in asyncio would block the event loop or require threading anyway. A dedicated thread is simpler and can be cancelled cooperatively.

### 3. SSE over WebSocket

**Decision:** Progress streaming uses SSE, not WebSocket.

**Rationale:** One-way communication is enough. SSE works with plain HTTP, has automatic reconnection in browsers, and is simpler to implement in FastAPI. WebSocket would be overkill.

### 4. Chunk-based AI extraction

**Decision:** Long texts are split into ~2500-word chunks before sending to the LLM.

**Rationale:** LLMs have token limits and lose attention on very long inputs. Chunking ensures each segment gets the model's full attention, improving recall.

### 5. Density-based term count

**Decision:** Target number of terms is computed as `ceil(words × terms_per_1k / 1000)`, capped by `num_terms`.

**Rationale:** A 10k-word chapter and a 100k-word book shouldn't yield the same number of terms. Density is intuitive and user-controllable.

### 6. No definitions in AI mode

**Decision:** In AI mode, definitions are extracted but not stored separately (they go into the glossary as `english_definition`), and they are not translated.

**Rationale:** (a) Definitions from the LLM are already high quality and don't need Wikipedia. (b) Translating them would double the cost. Users who want definitions translated can use Hybrid mode.

### 7. In-memory progress tracker

**Decision:** Progress events are kept in memory, not in the database.

**Rationale:** Events are ephemeral and only useful while the pipeline runs. Persisting them would add I/O overhead with no real benefit. History is bounded to 100 events for late subscribers.

### 8. Flexible metadata via JSON blob

**Decision:** Book metadata is stored as a JSON string column, not normalized columns.

**Rationale:** The metadata schema (from BookSpecsTemplate.json) may evolve. A JSON blob allows adding fields without migrations. Only the fields we use in prompts are parsed, and parsing is defensive.

### 9. `_source` marker → `metadata_source`

**Decision:** After early issues, the source marker (`manual` vs `json`) was moved from `_source` to `metadata_source` and persisted.

**Rationale:** The marker needs to survive a round-trip through the database. Persisting it makes the UI stateless and reliable.

### 10. Confirm dialog as Promise

**Decision:** `useConfirm()` returns a Promise, not a callback.

**Rationale:** Imperative `await confirm(...)` reads linearly, mirrors `window.confirm`, and avoids nested callbacks. Implemented via Zustand with a stored resolver.

---

## 🔒 Security & Privacy

### What stays local

- All source files
- All database content
- All exported files
- All cache

### What can leave the machine (only if user opts in)

- **LLM calls** — only when AI or Hybrid mode is used. Text chunks are sent to the chosen provider (OpenAI, etc.)
- **Wikipedia** — only for definition lookups (public queries)
- **Google Translate** — only in Offline mode with Google provider
- **LibreTranslate** — local server, nothing leaves
- **Argos** — fully offline, nothing leaves

### API keys

- Stored in plaintext in the SQLite database.
- **Accepted risk** for a single-user desktop app where the DB is only accessible to the current Windows user.
- If the app is later moved to a shared server, this must be replaced with OS keyring (`keyring` package) or secret storage.

### Uploads

- Allowed extensions: `.pdf`, `.docx`, `.epub`, `.txt`
- Max file size: 200 MB
- Filenames are sanitized; UUID prefix prevents collisions
- Path traversal is prevented by stripping directory components

---

## ⚡ Performance Considerations

### Backend

- **NLP is the bottleneck** — spaCy processes the full text. On ARM64, this is slower but acceptable.
- **LLM calls are network-bound** — batch where possible (translation).
- **Wikipedia lookups** have short timeouts (3s) and are best-effort.
- **SQLite** — single-writer; pipeline writes in one transaction at the end.

### Frontend

- **Code splitting** via Vite — routes are lazily loaded (future).
- **TanStack Query** caches project/glossary data; refetch on stale only.
- **Virtualization** is not yet used for large glossaries (up to ~1000 rows is fine).
- **SSE** has 15s keep-alive comments to avoid proxy timeouts.

### Storage

- Uploaded files are written once and read once per pipeline run.
- Translations are cached in diskcache, keyed by `(text, source, target, provider, model)`.

---

## 🧩 Extension Points

The following are designed to be swappable:

### Extractors

Add a new file format by:
1. Subclassing `DocumentExtractor` in `pipeline/extractors/`
2. Adding it to `_EXTRACTORS` in `loader.py`

### NLP sources

Add a new keyword source by:
1. Adding a function in `pipeline/nlp/candidates.py` that returns `list[Candidate]`
2. Adding it to `extract_keywords()` in `extractor.py`
3. Adding its weight in `scoring.py`

### Definition sources

Add a new source by:
1. Creating a module in `pipeline/definitions/` with a `fetch(term) -> str | None`
2. Adding it to `resolver.py` at the correct priority

### Translation providers

Add a new provider by:
1. Subclassing `Translator` in `pipeline/translation/`
2. Registering it in `service._PROVIDERS`

### LLM providers

Add a new provider by:
1. Adding an entry in `pipeline/definitions/llm_providers.json`
2. That's it — the OpenAI SDK handles it

---

## ⚠️ Known Limitations

1. **No OCR** — scanned PDFs produce no text. Users must use OCR before uploading.
2. **No folder linking** — files must be uploaded individually or in one batch.
3. **English-only source** — the NLP pipeline assumes English input.
4. **No translation memory across projects** — each project is independent.
5. **No LLM reflection** — the LLM is called once per chunk, not iteratively.
6. **Single-user** — no auth, no multi-tenancy.
7. **No Alembic migrations yet** — schema changes require deleting the DB.
8. **AI Mode score is synthetic** — since the LLM doesn't provide scores, they are computed from frequency.
9. **Progress events are in-memory** — if the backend restarts mid-pipeline, events are lost.
10. **Wikipedia lookups are serial** — could be parallelized for speed.

---

## 📖 Further Reading

- [USER_GUIDE.md](USER_GUIDE.md) — End-user guide (Persian)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Setup, testing, build
- [CHANGELOG.md](CHANGELOG.md) — Version history