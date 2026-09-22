# Testing Guide

> Complete reference for running, writing, and debugging tests in RakeGlossary.

**Status:** ✅ Backend (204 tests) · ✅ Frontend (150 tests)  
**Last updated:** 2026-09-21

---

## Table of Contents

- [Overview](#-overview)
- [Backend Tests (pytest)](#-backend-tests-pytest)
- [Frontend Tests (Vitest)](#-frontend-tests-vitest)
- [Shared Best Practices](#-shared-best-practices)
- [Common Failures & Fixes](#-common-failures--fixes)
- [Lessons Learned](#-lessons-learned)
- [CI/CD (D.11)](#-cicd-d11)

---

## 🎯 Overview

RakeGlossary uses two independent test suites:

| Suite | Framework | Location | Runner |
|---|---|---|---|
| Backend | pytest | `backend/tests/` | `python -m pytest` |
| Frontend | Vitest + React Testing Library | `frontend/tests/` | `npm test` |

**Guiding principles:**

1. **Fast feedback** — the whole suite runs in under 20 seconds.
2. **Isolation** — tests never depend on each other or on external services.
3. **Focus on behavior** — test what the component/function does, not how.
4. **Mock at boundaries** — mock API clients, hooks, and external services; keep the code under test real.

---

## 🐍 Backend Tests (pytest)

### Directory layout

```
backend/
├── app/                    # source code
├── tests/                  # ALL tests live here
│   ├── __init__.py
│   ├── conftest.py         # shared fixtures (session, TestClient, ...)
│   ├── test_extractors.py
│   ├── test_definitions.py
│   ├── test_translation.py
│   ├── test_nlp.py
│   ├── test_schemas.py
│   ├── test_db.py
│   ├── test_services_*.py  # one per service
│   ├── test_api_*.py       # one per API router
│   └── test_llm_extraction.py
└── pyproject.toml          # pytest config in [tool.pytest.ini_options]
```

### Prerequisites

```cmd
cd backend
pip install -e ".[dev]"
```

`dev` extra includes: `pytest`, `pytest-asyncio`, `respx`.

### Running tests

```cmd
REM All tests
python -m pytest tests/ -v

REM One file
python -m pytest tests/test_services_runner_ai.py -v

REM One test
python -m pytest tests/test_services_runner_ai.py::test_ai_pipeline_happy_path -v

REM Stop at first failure
python -m pytest tests/ -x

REM Show print/log output (loguru captures by default)
python -m pytest tests/ -v -s

REM Run tests matching a pattern
python -m pytest tests/ -k "ai_pipeline" -v
```

**Expected output (current):**

```
============================= 204 passed, 2 warnings in ~15s =============================
```

### Test organization

| File | Covers |
|---|---|
| `test_extractors.py` | PDF / DOCX / EPUB / TXT extraction |
| `test_definitions.py` | In-text / Wikipedia / WordNet resolution |
| `test_translation.py` | Translation service + cache |
| `test_nlp.py` | Keyword extraction (spaCy + RAKE + YAKE) |
| `test_schemas.py` | Pydantic I/O contracts |
| `test_db.py` | ORM models + cascades |
| `test_services_*.py` | Service layer (project, source, glossary, export, settings, runner, ...) |
| `test_api_*.py` | HTTP endpoints via `TestClient` |
| `test_llm_extraction.py` | LLM client (mocked HTTP via `respx`) |
| `test_rate_limiter.py` | Rate limiting utility |
| `test_api_meta.py` | `/api/health` and `/api/about` (D.8) |

### Shared fixtures (`conftest.py`)

Typical fixtures you'll use:

```python
# Session: in-memory SQLite, isolated per test
def test_something(session: Session) -> None:
    ...

# HTTP client: FastAPI TestClient (in-process)
def test_endpoint(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
```

If you need a new fixture, add it to `conftest.py` (not individual test files) so it's available everywhere.

### Mocking strategies

**Mock at the boundary, not the internals.**

Good:
```python
with patch("app.services.pipeline_runner.llm_client.extract_terms_llm",
           side_effect=RuntimeError("api down")):
    ...
```

Bad:
```python
# Don't mock the DB — use the real one (in-memory)
```

**Patching target rules:**

The `patch` target is the **import path from the module where the name is used**, not where it's defined. If `pipeline_runner.py` does:

```python
from app.pipeline import llm_client
...
llm_client.extract_terms_llm(...)
```

then patch `app.services.pipeline_runner.llm_client.extract_terms_llm` (where `llm_client` is looked up). Patching `app.pipeline.llm_client.extract_terms_llm` would work only if you patched it before the import.

**`respx` for HTTP:**

```python
import respx
from httpx import Response

@respx.mock
def test_wikipedia_lookup() -> None:
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json={"query": {"pages": {...}}})
    )
    ...
```

### Coverage (optional)

```cmd
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run from `backend/` folder, venv active |
| `IndentationError` after editing | Watch for tabs mixed with spaces |
| `assert DONE == FAILED` | Check that the code under test actually raises |
| `pytest: command not found` | Use `python -m pytest` |
| Fixture not found | Move it to `conftest.py` |
| Slow tests | Run only the failing file with `-x` |

---

## ⚛️ Frontend Tests (Vitest)

### Directory layout

Tests **mirror** the `src/` structure, but live in a sibling folder:

```
frontend/
├── src/                                # source code
│   ├── components/layout/Sidebar.tsx
│   └── features/settings/components/AboutPanel.tsx
├── tests/                              # ALL tests live here
│   ├── setup.ts                        # global setup (jest-dom + cleanup)
│   ├── components/
│   │   └── layout/
│   │       └── Sidebar.test.tsx
│   ├── features/
│   │   ├── settings/components/
│   │   │   ├── AboutPanel.test.tsx
│   │   │   ├── StopwordsManager.test.tsx
│   │   │   ├── LlmSettings.test.tsx
│   │   │   └── LlmQuickSetupDialog.test.tsx
│   │   ├── sources/components/
│   │   │   ├── SourcesPanel.test.tsx
│   │   │   ├── SourceItem.test.tsx
│   │   │   └── MultiFileDropzone.test.tsx
│   │   ├── glossary/components/
│   │   │   └── GlossaryTable.test.tsx
│   │   └── progress/
│   │       ├── components/ProgressLog.test.tsx
│   │       └── hooks/useProgressStream.test.tsx
│   ├── hooks/
│   │   └── useAbout.test.tsx
│   └── pages/
│       ├── SettingsPage.test.tsx
│       ├── ProjectsPage.test.tsx
│       └── ProjectDetailPage.test.tsx
└── vitest.config.ts                    # test runner config
```

**Rule:** never put `*.test.tsx` files inside `src/`. Keep them in `tests/`.

### Prerequisites

```cmd
cd frontend
npm install
```

Already installed (as `devDependencies`):

- `vitest`, `@vitest/ui`
- `jsdom`
- `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`

### Running tests

```cmd
REM All tests, one shot (CI mode)
npm test

REM Watch mode (re-runs on save)
npm run test:watch

REM Interactive UI in the browser
npm run test:ui

REM Single file
npx vitest run tests/pages/SettingsPage.test.tsx

REM Pattern
npx vitest run -t "settings"

REM Verbose
npx vitest run --reporter=verbose

REM Coverage
npx vitest run --coverage
```

**Expected output (current):**

```
 Test Files  15 passed (15)
      Tests  150 passed (150)
```

### `vitest.config.ts`

```ts
/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), 'src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    css: false,
    include: ['tests/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist'],
  },
})
```

**Critical points:**

- `include` points to `tests/`, not `src/`.
- `alias` uses `process.cwd()`, not `import.meta.dirname` (which is broken in Vite 8 with rolldown).
- `css: false` speeds up tests significantly (Tailwind CSS is not needed at runtime).
- `setupFiles` loads `@testing-library/jest-dom/vitest` matchers + auto-cleanup.

### `tests/setup.ts`

```ts
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})
```

### Mocking strategies

The frontend tests rely heavily on `vi.mock()` to isolate components. Here are the patterns we use.

#### 1. Mocking a hook

```tsx
const mockUseAbout = vi.fn()
vi.mock('@/hooks/useAbout', () => ({
  useAbout: () => mockUseAbout(),
}))

// In a test:
mockUseAbout.mockReturnValue({ data: mockAbout })
```

#### 2. Mocking a child component

```tsx
vi.mock('@/features/progress/components/ProgressLog', () => ({
  ProgressLog: ({ connected }: { connected: boolean }) => (
    <div data-testid="progress-log" data-connected={String(connected)} />
  ),
}))
```

**Rule:** mocks should render minimal, deterministic DOM. Use `data-testid` liberally.

#### 3. Mocking i18n

```tsx
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
    i18n: { language: 'fa', changeLanguage: vi.fn() },
  }),
}))
```

The `t()` mock returns the **key** so tests can assert against `about.title` instead of hardcoded Persian text.

#### 4. Mocking react-router

```tsx
// Simple: use MemoryRouter in render
render(
  <MemoryRouter>
    <ComponentUnderTest />
  </MemoryRouter>
)

// Full control: mock useNavigate / useParams
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'proj-1' }),
  }
})
```

#### 5. Wrapping with QueryClient

```tsx
function renderWithQuery(ui: ReactNode) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}
```

`retry: false` is **mandatory** for tests — otherwise a mocked rejection retries for 1s.

#### 6. Mocking UI primitives (Radix)

Some Radix components require complex setup (portals, focus traps). Mock them:

```tsx
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div data-testid="dialog-root">{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  // ...
}))
```

**Pattern:** keep the semantic shape (open/closed, children) but drop the rendering details.

#### 7. `lucide-react` brand icon gotcha

Since Lucide v0.400+, brand icons (`Github`, `Twitter`, `Linkedin`, `Facebook`, `Instagram`) have been **removed**. Use generic icons instead (`Code`, `Briefcase`, `Globe`, `Mail`).

#### 8. Accessing buttons whose label is in a `Tooltip`

**Problem:** `screen.getByTitle('common.delete')` fails because the `title` is on the Tooltip wrapper, not on the Button.

**Solutions (preferred order):**

1. **Add `aria-label` to the button in the source** (best for accessibility). Then test with `screen.getByLabelText('delete')`.
2. **Find by lucide icon class:**

```tsx
const deleteBtn = container
  .querySelector('.lucide-trash-2')
  ?.closest('button') as HTMLButtonElement
```

3. **Add `data-testid` to the button in the source.**

### Common patterns

#### `userEvent.setup()` (preferred)

```tsx
const user = userEvent.setup()
await user.click(screen.getByText('Save'))
await user.type(input, 'hello{Enter}')
```

#### `fireEvent` for edge cases

`userEvent` is asynchronous and validates "realistic" interactions. For non-realistic events (like dispatching a specific `keyDown`), use `fireEvent`:

```tsx
fireEvent.keyDown(input, { key: 'Enter' })
fireEvent.scroll(container)
fireEvent.change(input, { target: { value: 'کتاب' } })  // bypass char-by-char
```

#### `waitFor` and `findBy`

```tsx
// Wait for a specific state
await waitFor(() => expect(result.current.isSuccess).toBe(true))

// Or use findBy (implicit wait)
const element = await screen.findByText('Loaded')
```

#### `act()` for direct state updates

When you call a callback directly (e.g., a captured `onEvent`), wrap in `act`:

```tsx
act(() => {
  capturedCallbacks?.onEvent({ ... })
})
```

#### Overriding jsdom layout properties

jsdom doesn't lay out elements: `scrollHeight`, `clientHeight`, `clientWidth` are always `0`. For components that read them (like `ProgressLog`):

```tsx
Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
  configurable: true,
  get: () => 1000,
})
Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  configurable: true,
  get: () => 200,
})

// And per-instance for `scrollTop`:
Object.defineProperty(container, 'scrollTop', {
  configurable: true,
  value: 0,
  writable: true,
})
```

### Coverage (optional)

```cmd
npm install -D @vitest/coverage-v8
npx vitest run --coverage
```

Add to `vitest.config.ts`:

```ts
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'html'],
    include: ['src/**/*.{ts,tsx}'],
    exclude: ['src/**/*.d.ts', 'src/main.tsx'],
  },
}
```

### Troubleshooting

| Symptom | Fix |
|---|---|
| `Failed to resolve import "@/..."` | Alias is misconfigured. Check `vitest.config.ts`. |
| `Not wrapped in act(...)` | Wrap direct state updates in `act()`. |
| `Found multiple elements with the text` | Use `getAllByText`, or narrow by role/testid. |
| `Unable to find element with title X` | Title is inside Tooltip mock; find by icon class instead. |
| Test times out (5000ms) | `retry` is not `false` in QueryClient. |
| `Cannot read property 'scrollHeight'` | Override jsdom properties as shown above. |
| `jsdom was created N times` warning | Harmless. See "Performance" below. |

### Performance note

Vitest creates a fresh jsdom environment per test file by default. That's the source of the `jsdom was created 15 times` warning. To share it (2-3× faster):

```ts
// vitest.config.ts
test: {
  pool: 'vmThreads',
  isolate: false,   // <- shares environment between files
}
```

**Trade-off:** shared state between files. Only safe if all tests properly `cleanup()` (which ours do via `tests/setup.ts`).

---

## 🧭 Shared Best Practices

### Test naming

Follow AAA (Arrange → Act → Assert):

```tsx
it('calls onDelete with entry id when delete button is clicked', async () => {
  // Arrange
  const onDelete = vi.fn()
  render(<Component onDelete={onDelete} />)
  // Act
  await user.click(screen.getByText('delete'))
  // Assert
  expect(onDelete).toHaveBeenCalledWith(99)
})
```

Describe blocks should state the **unit under test**; `it` blocks should state the **expected behavior** in plain English.

### One assertion focus per test

Prefer multiple `it` blocks over one big test with 20 assertions. Failures point to exactly one behavior.

### Don't test implementation details

Bad:
```tsx
expect(component.state.loading).toBe(true)   // private state
```

Good:
```tsx
expect(screen.getByText('common.loading')).toBeInTheDocument()
```

### Mock at boundaries

- ✅ Mock API clients (`fetchAbout`, `llmApi`)
- ✅ Mock hooks (`useSources`, `useGlossary`)
- ✅ Mock i18n, toast, confirm
- ❌ Don't mock React Query, React Router, or the component under test
- ❌ Don't mock low-level things like `useState`

### Always `vi.clearAllMocks()` in `beforeEach`

Prevents cross-test contamination.

### Keep tests deterministic

- No `Date.now()` without mocking
- No `Math.random()` without mocking
- No real network calls

### Test errors, not just happy paths

Every flow has at least 3 tests:

1. Success
2. User cancels / rejects
3. API failure

---

## 🐛 Common Failures & Fixes

### Backend

**`AssertionError: assert DONE == FAILED`**

The pipeline swallowed an exception and returned success. Look for a `try/except` that returns `[]` instead of re-raising. Fix by raising after the loop if the result is empty.

**`IndentationError: unindent does not match`**

Copy-paste from chat introduces tabs. Ensure `if` blocks match parent indentation exactly (4 spaces).

### Frontend

**`Uncaught SyntaxError: The requested module 'lucide-react' does not provide an export named 'Github'`**

Lucide removed brand icons. Replace with generic icons (`Code`, `Briefcase`).

**`Failed to run dependency scan` with all imports failing**

`vite.config.ts` alias is broken. Use `path.resolve(process.cwd(), 'src')` — not `import.meta.dirname`.

**Test file has a `.ts.txt` or `.js` duplicate**

Vite/Vitest picks the **first** config file it finds. Ensure only one `vitest.config.ts` exists.

**`Cannot use import statement outside a module`**

`setup.ts` is being loaded as CommonJS. Verify `"type": "module"` is in `package.json`.

---

## 📚 Lessons Learned

These are real bugs we hit and fixed during D.8–D.10. Keep them in mind.

1. **Always verify the full folder listing before debugging imports.**
   A stray `vite.config.js` (leftover) can override `vite.config.ts` silently.

2. **`import.meta.dirname` is unreliable in Vite 8 configs.**
   Use `process.cwd()` or `fileURLToPath(new URL(..., import.meta.url))`.

3. **Empty `try/except` in pipelines hides real failures.**
   Always re-raise (or explicitly mark the project as `FAILED`) when the result set is empty.

4. **`retry: 1` in React Query hooks breaks tests.**
   Always set `retry: false` in the test QueryClient, or don't hardcode retry in hooks.

5. **Lucide removed brand icons in v0.400+.**
   Use generic icons for GitHub/LinkedIn/etc.

6. **Tooltip titles are not accessible in tests via `getByTitle`.**
   Prefer `aria-label` on the actual button, or query by lucide icon class.

7. **jsdom doesn't lay out elements.**
   Override `scrollHeight` / `clientHeight` / `scrollTop` when testing scroll behavior.

8. **`act()` is mandatory when calling captured callbacks directly.**
   Any state change triggered outside React's event system needs `act()`.

---

## 🚀 CI/CD (D.11)

The next step (D.11) will add GitHub Actions workflows:

- `.github/workflows/backend-ci.yml` — runs `pytest`, `ruff`, `mypy` on Windows + Ubuntu
- `.github/workflows/frontend-ci.yml` — runs `tsc`, `oxlint`, `vitest` on Node 24

See `docs/ROADMAP.md` for the full plan.

---

## 🔗 Further Reading

- [README.md](../README.md) — Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Setup, code style, adding features
- [ROADMAP.md](ROADMAP.md) — Future plans (D.11 onward)
- [Vitest docs](https://vitest.dev/)
- [Testing Library docs](https://testing-library.com/docs/react-testing-library/intro/)
- [pytest docs](https://docs.pytest.org/)