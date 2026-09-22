# Developer Guide

> Setup, testing, and build instructions for RakeGlossary developers.

## Table of Contents

- [Prerequisites](#-prerequisites)
- [Project Structure](#-project-structure)
- [Initial Setup](#-initial-setup)
- [Running in Development](#-running-in-development)
- [Testing](#-testing)
- [Code Style](#-code-style)
- [Adding a Feature](#-adding-a-feature)
- [Database Changes](#-database-changes)
- [Frontend Development](#-frontend-development)
- [Backend Development](#-backend-development)
- [Packaging for Windows](#-packaging-for-windows)
- [Troubleshooting](#-troubleshooting)
- [Useful Scripts](#-useful-scripts)

---

## 📋 Prerequisites

| Tool | Version | Notes |
|---|---|---|
| **Python** | 3.12 | 3.11 also works. Do not use < 3.11. |
| **Node.js** | 20+ | Vite requires Node 18+. |
| **Git** | any recent | Optional but recommended. |
| **OS** | Windows 10/11 | Developed and tested on Windows, ARM64 included. |

**Note for ARM64 (Snapdragon X, etc.):**
- Use the ARM64 build of Python 3.12.
- `spaCy` wheels are available for ARM64 via Conda (see below).
- `PyMuPDF` ships `windows-arm64` wheels from version 1.28.

---

## 📂 Project Structure

```
RakeGlossary/
├── backend/                # Python + FastAPI
│   ├── app/
│   ├── tests/
│   └── pyproject.toml
├── frontend/               # React + TypeScript
│   ├── src/
│   ├── index.html
│   └── package.json
├── scripts/                # Windows batch helpers
├── docs/                   # This documentation
├── data/                   # Runtime data (git-ignored)
└── README.md
```

---

## ⚙ Initial Setup

### Option A — Automated (recommended)

Double-click `scripts\setup.bat`. It will:

1. Locate or create a Python venv at `..\venv312` (i.e. next to the project).
2. Install backend dependencies via `pip install -e ".[dev]"`.
3. Download the spaCy English model (`en_core_web_sm`).
4. Download NLTK data (`stopwords`, `punkt`, `punkt_tab`).
5. Run `npm install` in `frontend/`.

**Time:** 5–10 minutes depending on connection speed.

### Option B — Manual

```cmd
REM --- 1. Create and activate a venv ---
cd C:\projects\Translation\RAKE
py -3.12 -m venv venv312
.\venv312\Scripts\activate.bat

REM --- 2. Install backend ---
cd RakeGlossary\backend
pip install -e ".[dev]"

REM --- 3. spaCy model ---
python -m spacy download en_core_web_sm

REM --- 4. NLTK data ---
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

REM --- 5. Frontend ---
cd ..\frontend
npm install
```

### Verifying the setup

From the backend folder:

```cmd
python -m pytest tests/ -v
```

Expected: **all tests pass** (currently ~200).

---

## 🚀 Running in Development

### Both servers at once

Double-click `scripts\dev.bat`. This opens two new windows:

- **Backend:** Uvicorn reload server on `http://127.0.0.1:8765`
- **Frontend:** Vite dev server on `http://localhost:5173`

Close both windows to stop.

### Backend only

```cmd
scripts\dev-backend.bat
```

- Watches `backend/` for changes (via Uvicorn's `--reload`).
- API docs at `http://127.0.0.1:8765/docs`.

### Frontend only

```cmd
scripts\dev-frontend.bat
```

- Vite HMR is enabled — most changes hot-reload without a full refresh.
- Proxy: `/api/*` requests are forwarded to `http://127.0.0.1:8765`.

### Interactive shell

```cmd
scripts\cmd.bat
```

Opens a `cmd` with the venv activated and CWD at `backend/`.

---

## 🧪 Testing

Tests live in `backend/tests/` and use **pytest**.

### Run all tests

```cmd
cd backend
python -m pytest tests/ -v
```

### Run a single file

```cmd
python -m pytest tests/test_llm_extraction.py -v
```

### Run a single test

```cmd
python -m pytest tests/test_llm_extraction.py::test_extract_parses_valid_response -v
```

### Show stdout

```cmd
python -m pytest tests/ -v -s
```

Useful for debugging because our pipeline emits logs via `loguru`.

### Show `loguru` warnings during tests

By default, `loguru` output is captured. Use `-s` (above) to see it.

### Test structure

| File | Covers |
|---|---|
| `test_extractors.py` | PDF / DOCX / EPUB / TXT extraction |
| `test_definitions.py` | In-text / Wikipedia / WordNet resolution |
| `test_translation.py` | Translation service + cache |
| `test_nlp.py` | Keyword extraction (spaCy + RAKE + YAKE) |
| `test_schemas.py` | Pydantic I/O contracts |
| `test_db.py` | ORM models + cascades |
| `test_services_*.py` | Service layer (project, source, glossary, export, settings, runner) |
| `test_api_*.py` | HTTP endpoints (via `TestClient`) |
| `test_llm_extraction.py` | LLM client (mocked HTTP) |

### Frontend tests

Not yet implemented. When added, use **Vitest** (already compatible with Vite).

---

## 🎨 Code Style

### Backend

- **Formatter:** `black` (line length 100)
- **Linter:** `ruff`
- **Type checker:** `mypy`

```cmd
cd backend
ruff check app/
black app/
mypy app/
```

Config in `backend/pyproject.toml`.

### Frontend

- **Formatter:** none enforced yet (Prettier recommended)
- **Linter:** ESLint (from Vite template)

```cmd
cd frontend
npm run lint
```

### General conventions

- **Backend:** `snake_case` for functions/variables, `PascalCase` for classes.
- **Frontend:** `camelCase` for variables/functions, `PascalCase` for components/types.
- **CSS:** Tailwind utility classes; CSS variables for theming.
- **No comments** unless they explain *why*, not *what*.

---

## ➕ Adding a Feature

### Typical flow

1. **Backend first.** Add models/schemas/services/routes.
2. **Add tests.** Cover happy path + at least one error case.
3. **Frontend second.** Add types, API calls, hooks, components.
4. **Manual test.** Run `scripts\dev.bat` and verify.
5. **Update docs** if user-facing.

### Example: add a new endpoint

1. Add a Pydantic schema in `app/schemas/`.
2. Add a service function in `app/services/`.
3. Add a router in `app/api/`.
4. Register the router in `app/api/__init__.py` and `app/main.py`.
5. Add tests in `tests/test_api_*.py`.

### Example: add a new UI page

1. Create `src/pages/MyPage.tsx`.
2. Add a route in `App.tsx`.
3. Add a sidebar link in `components/layout/Sidebar.tsx`.
4. Add translations in `i18n/fa.ts` and `i18n/en.ts`.
5. Add types/API calls in `src/api/` and `src/types/`.

---

## 🗄 Database Changes

**We do not use Alembic yet.** When you change a model:

1. Stop the backend.
2. Delete `data/rakeglossary.db`.
3. Delete `data/projects/` (optional — only if source files changed schema).
4. Restart the backend.

The database is recreated automatically via `Base.metadata.create_all()`.

**This is acceptable while the app is personal.** Before public release, add Alembic.

### Example: adding a column

```python
# In app/models/project.py
class Project(Base):
    ...
    new_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

Then:
1. Add the field to the Pydantic schema (`schemas/project.py`).
2. Update the service layer if needed.
3. Update tests if needed.
4. Delete the DB and restart.

---

## ⚛ Frontend Development

### Path aliases

The Vite config defines `@` as the `src/` root:

```ts
import { Button } from '@/components/ui/button'
```

This works in TypeScript and Vite. Do not use relative paths like `../../components/...` unless inside the same folder.

### Theming

Use CSS variables, not hardcoded colors:

```tsx
<div style={{
  backgroundColor: 'rgb(var(--color-surface))',
  color: 'rgb(var(--color-text))',
}} />
```

For opacity modifiers:

```tsx
'rgb(var(--color-primary) / 0.5)'
```

To add a new theme:

1. Add a `[data-theme="my-theme"]` block in `src/styles/themes.css`.
2. Add it to `THEMES` in `src/features/settings/settingsStore.ts`.
3. Nothing else — components pick up the new variables automatically.

### i18n

Add keys to **both** `src/i18n/fa.ts` and `src/i18n/en.ts`:

```ts
// fa.ts
myFeature: { title: 'عنوان من' }

// en.ts
myFeature: { title: 'My Title' }
```

Then use in components:

```tsx
const { t } = useTranslation()
<h1>{t('myFeature.title')}</h1>
```

### Adding a shadcn-style primitive

1. Create `src/components/ui/my-component.tsx`.
2. Export a component with `React.forwardRef`.
3. Use `cn()` from `@/lib/utils` to merge class names.
4. Keep it headless if possible — styling belongs to consumers.

### RTL handling

- The app is `dir="rtl"` when Persian is selected.
- Use logical Tailwind properties: `ms-*`, `me-*`, `ps-*`, `pe-*` (not `ml-*`).
- To force a specific direction on a component, use `dir="ltr"` or `dir="rtl"` locally.

---

## 🐍 Backend Development

### Adding a new extractor

1. Subclass `DocumentExtractor` in `app/pipeline/extractors/`.
2. Set `supported_extensions = ('.ext',)`.
3. Implement `extract(self, path: Path) -> str`.
4. Register in `loader.py`'s `_EXTRACTORS`.
5. Add a test in `tests/test_extractors.py`.

### Adding a new translation provider

1. Subclass `Translator` in `app/pipeline/translation/`.
2. Set `name = 'my-provider'`.
3. Implement `translate(self, text, source, target) -> str`.
4. Add it to `service._PROVIDERS`.
5. Update the frontend dropdown in `OptionsPanel.tsx`.

### Adding a new LLM provider

1. Edit `app/pipeline/definitions/llm_providers.json`.
2. Add an entry with `key`, `name`, `base_url`, `default_model`, `suggested_models`, `docs_url`.
3. Restart the backend. The frontend fetches the list from `/api/settings/llm/providers`.

No Python code changes needed — the OpenAI SDK handles all providers via `base_url`.

### Logging

Use `loguru` via the `get_logger` helper:

```python
from app.core.logging import get_logger

log = get_logger("services.my_service")
log.info("Something happened")
log.warning("Something suspicious")
log.exception("Something failed")  # includes traceback
```

Logs go to both console (colorized) and `data/logs/rakeglossary.log` (rotating).

---

## 📦 Packaging for Windows

> **Status:** planned, not yet implemented.

### Planned approach

1. **`pywebview`** — wraps the React build in a native window (WebView2).
2. **PyInstaller** — bundles Python + backend into a single `.exe`.
3. **Inno Setup** — creates a Windows installer.

### Rough outline

```python
# desktop/launcher.py
import webview
import threading
import uvicorn
from app.main import app

def start_backend():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")

if __name__ == "__main__":
    threading.Thread(target=start_backend, daemon=True).start()
    webview.create_window("RakeGlossary", "frontend/dist/index.html")
    webview.start()
```

Then:

```cmd
REM 1. Build frontend
cd frontend
npm run build

REM 2. Bundle backend + frontend
cd ..\backend
pyinstaller --onefile --add-data "..\frontend\dist;frontend\dist" ..\desktop\launcher.py
```

**ARM64 note:** PyInstaller supports ARM64 as of 6.x, but some third-party hooks may need adjustment. Test early.

---

## 🔧 Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

You are not inside the `backend/` folder, or the venv is not active.

```cmd
cd backend
python -c "from app.main import app; print('OK')"
```

### `Port 8765 is already in use`

Another backend is running. Kill it:

```powershell
Get-Process python | Stop-Process -Force
```

### `openai` not found inside venv

Make sure the correct venv is active:

```powershell
python -c "import sys; print(sys.executable)"
```

Should print the path to `venv312\Scripts\python.exe`.

If not, activate it:

```cmd
..\venv312\Scripts\activate.bat
```

### `pytest: command not found`

Use `python -m pytest` instead:

```cmd
python -m pytest tests/ -v
```

### spaCy model missing

```cmd
python -m spacy download en_core_web_sm
```

On ARM64, prefer Conda:

```cmd
conda install -c conda-forge spacy
python -m spacy download en_core_web_sm
```

### NLTK data missing

```cmd
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

If behind a proxy:

```cmd
set NLTK_ALLOW_PROXIED_URLOPEN=1
```

### Vite HMR not picking up changes

Restart the Vite dev server, or clear the cache:

```cmd
cd frontend
Remove-Item -Recurse -Force node_modules\.vite
npm run dev
```

### CSS changes not visible

Hard refresh in the browser: `Ctrl+Shift+R`.

If the issue persists, check the browser console for syntax errors in CSS.

---

## 🛠 Useful Scripts

| Script | Purpose |
|---|---|
| `scripts\setup.bat` | One-time dependency setup |
| `scripts\dev.bat` | Run both backend + frontend in separate windows |
| `scripts\dev-backend.bat` | Backend only |
| `scripts\dev-frontend.bat` | Frontend only |
| `scripts\cmd.bat` | Interactive `cmd` with venv activated |

### Running commands from the wrong folder

A frequent source of confusion: `python -c "from app..."` only works from the `backend/` folder, because `app` is a top-level package there.

Use `scripts\cmd.bat` to always start in the right place.

---

## 📚 Further Reading

- [README.md](../README.md) — Project overview
- [USER_GUIDE.md](USER_GUIDE.md) — End-user guide (Persian)
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [CHANGELOG.md](CHANGELOG.md) — Version history