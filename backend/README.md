# RakeGlossary — Backend

> FastAPI backend for RakeGlossary — document extraction, NLP keyword extraction, definition resolution, and translation.

## Overview

This package contains the entire backend of RakeGlossary: the HTTP API, the SQLite data layer, and the glossary generation pipeline.

It is designed to be run locally on `127.0.0.1:8765` and consumed by the React frontend.

## Structure

```
app/
├── api/                # FastAPI routers (thin HTTP layer)
├── core/               # Config, logging, DB, version
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic v2 schemas (I/O contracts)
├── services/           # Business logic + orchestration
└── pipeline/           # Glossary generation pipeline
    ├── extractors/     # PDF / DOCX / EPUB / TXT → text
    ├── nlp/            # text → candidate keywords
    ├── definitions/    # keyword → definition
    ├── translation/    # text → Persian
    ├── glossary.py     # Core orchestrator
    └── llm_client.py   # Unified LLM interface
```

## Installation

From this folder, with the shared venv active:

```cmd
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

Or, from the project root:

```cmd
scripts\setup.bat
```

## Running

```cmd
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

Or from the project root:

```cmd
scripts\dev-backend.bat
```

- **API:** http://127.0.0.1:8765
- **Swagger UI:** http://127.0.0.1:8765/docs
- **ReDoc:** http://127.0.0.1:8765/redoc
- **Health:** http://127.0.0.1:8765/api/health
- **About:** http://127.0.0.1:8765/api/about

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/about` | App metadata (version, author, tech stack) |
| POST | `/api/projects` | Create an empty project |
| GET | `/api/projects` | List projects (paginated) |
| GET | `/api/projects/{id}` | Get a single project |
| PATCH | `/api/projects/{id}` | Update title / options |
| DELETE | `/api/projects/{id}` | Delete project + sources + entries |
| PUT | `/api/projects/{id}/metadata` | Set book metadata |
| DELETE | `/api/projects/{id}/metadata` | Clear book metadata |
| GET | `/api/projects/{id}/sources` | List sources |
| POST | `/api/projects/{id}/sources/upload` | Upload one or more files |
| POST | `/api/projects/{id}/sources/text` | Add a text snippet |
| PATCH | `/api/projects/{id}/sources/{sid}` | Rename / toggle inclusion |
| DELETE | `/api/projects/{id}/sources/{sid}` | Delete source |
| GET | `/api/projects/{id}/glossary` | List glossary entries |
| PATCH | `/api/glossary/{eid}` | Update entry (manual edit) |
| DELETE | `/api/glossary/{eid}` | Delete entry |
| POST | `/api/process/{id}` | Start pipeline (background thread) |
| POST | `/api/process/{id}/cancel` | Cancel running pipeline |
| GET | `/api/process/{id}/events` | SSE progress stream |
| GET | `/api/export/{id}/{fmt}` | Download CSV / XLSX / TBX |
| GET | `/api/settings` | List all settings |
| GET/PUT/DELETE | `/api/settings/{key}` | Manage a setting |
| GET/POST | `/api/settings/stopwords` | Global user blacklist |
| DELETE | `/api/settings/stopwords/{word}` | Remove from blacklist |
| GET | `/api/settings/llm/providers` | List LLM providers |
| GET/PUT/DELETE | `/api/settings/llm` | LLM configuration |
| POST | `/api/settings/llm/test` | Test LLM connection |

## Pipeline Modes

| Mode | Definition | Translation | Cost |
|---|---|---|---|
| **offline** | In-Text → Wikipedia → WordNet | Argos (offline) | Free |
| **hybrid** | In-Text → Wikipedia → WordNet | LLM (context-aware) | Half of AI |
| **ai** | LLM (chunk-based, rich prompt) | LLM (context-aware) | ~$0.01 / 100 terms |

## Configuration

Settings are loaded from environment variables with defaults. See `app/core/config.py`.

| Variable | Default | Purpose |
|---|---|---|
| `RG_HOST` | `127.0.0.1` | Bind address |
| `RG_PORT` | `8765` | Bind port |
| `RG_LOG_LEVEL` | `INFO` | Log level |
| `RG_NUM_TERMS` | `500` | Default max terms |
| `RG_TRANSLATION_PROVIDER` | `google` | Default translator |
| `RG_LIBRE_URL` | `http://127.0.0.1:5000` | LibreTranslate endpoint |
| `RG_WIKI_API` | `https://en.wikipedia.org/w/api.php` | Wikipedia API |
| `RG_WIKI_TIMEOUT` | `3.0` | Wikipedia request timeout (s) |
| `RG_HTTP_TIMEOUT` | `8.0` | General HTTP timeout (s) |
| `RG_TRANSLATION_RATE_LIMIT` | `4.0` | Requests per second |
| `RG_TRANSLATION_MAX_RETRIES` | `4` | Retry attempts |
| `RG_TRANSLATION_BATCH_SIZE` | `25` | Items per batch |
| `RG_LLM_TIMEOUT` | `30.0` | LLM request timeout (s) |
| `RG_LLM_MAX_TOKENS` | `80` | Max tokens for definitions |
| `RG_LLM_TEMPERATURE` | `0.3` | LLM temperature |
| `NLTK_ALLOW_PROXIED_URLOPEN` | `1` | Allow NLTK downloads behind proxy |

## Storage Layout

All runtime data lives in `../data/`:

```
data/
├── rakeglossary.db           # SQLite database
├── projects/                 # Uploaded files (per project)
│   └── {title}__{id8}/
├── exports/                  # Temporary export files
├── cache/translations/       # diskcache for translation cache
└── logs/rakeglossary.log     # Rotating log (10 MB × 14 days)
```

## Testing

```cmd
python -m pytest tests/ -v
```

**Coverage:**

| Area | Test file |
|---|---|
| Extractors | `test_extractors.py` |
| Definitions | `test_definitions.py` |
| Translation | `test_translation.py` |
| NLP | `test_nlp.py` |
| Schemas | `test_schemas.py` |
| DB models | `test_db.py` |
| Services | `test_services_*.py` |
| API | `test_api_*.py` |
| LLM client | `test_llm_extraction.py` |

## Code Quality

```cmd
ruff check app/
black app/
mypy app/
```

Configuration is in `pyproject.toml`.

## Dependencies

**Core:**
- `fastapi`, `uvicorn` — HTTP server
- `sqlalchemy` — ORM
- `pydantic` — schemas
- `loguru` — logging

**Document extraction:**
- `pymupdf` — PDF
- `python-docx` — DOCX
- `ebooklib` + `beautifulsoup4` — EPUB
- `charset-normalizer` — TXT encoding detection

**NLP:**
- `spacy` (with `en_core_web_sm`)
- `nltk`, `rake-nltk`
- `yake`

**Translation:**
- `deep-translator` — Google, LibreTranslate
- `argostranslate` — fully offline

**LLM:**
- `openai` — SDK for OpenAI and OpenAI-compatible providers

**Export:**
- `openpyxl` — XLSX

See `pyproject.toml` for exact versions.

## Adding a New LLM Provider

Edit `app/pipeline/definitions/llm_providers.json` and add an entry:

```json
{
  "key": "my-provider",
  "name": "My Provider",
  "base_url": "https://api.my-provider.com/v1",
  "default_model": "my-model",
  "suggested_models": ["my-model", "my-model-pro"],
  "docs_url": "https://my-provider.com/keys"
}
```

No Python changes needed. The frontend fetches the list from `/api/settings/llm/providers`.

## Adding a New Extractor

1. Create `app/pipeline/extractors/my_format.py`
2. Subclass `DocumentExtractor`
3. Set `supported_extensions` and implement `extract(path) -> str`
4. Register in `loader.py`'s `_EXTRACTORS`
5. Add a test in `tests/test_extractors.py`

## License

MIT — see [../LICENSE](../LICENSE).