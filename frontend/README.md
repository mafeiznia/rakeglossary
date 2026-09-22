# RakeGlossary — Frontend

> React + TypeScript + Vite frontend for RakeGlossary.

## Overview

This package is the user interface of RakeGlossary. It talks to the FastAPI backend on `127.0.0.1:8765` through a Vite dev proxy in development, and directly in production.

Features:

- Bilingual (Persian RTL / English LTR) via `i18next`
- 5 color themes via CSS custom properties
- Live progress via Server-Sent Events (SSE)
- Inline-editable glossary table
- Server state via TanStack Query
- App preferences (theme, language) persisted in `localStorage`

## Structure

```
src/
├── api/                # HTTP client + typed endpoints
├── components/
│   ├── ui/             # Primitives (Button, Input, Dialog, ...)
│   └── layout/         # AppLayout, Header, Sidebar
├── features/           # Feature-scoped modules
│   ├── projects/
│   ├── sources/
│   ├── glossary/
│   ├── progress/
│   ├── metadata/
│   ├── settings/
│   └── confirm/
├── pages/              # Route-level components
├── i18n/               # fa.ts / en.ts / index.ts
├── types/              # Shared TypeScript types
├── lib/                # Pure helpers + query client
├── styles/             # themes.css
├── App.tsx             # Router + providers
└── main.tsx            # React root
```

## Installation

```cmd
npm install
```

Or from the project root:

```cmd
scripts\setup.bat
```

## Running in Development

```cmd
npm run dev
```

Or from the project root:

```cmd
scripts\dev-frontend.bat
```

- **URL:** http://localhost:5173
- The dev server proxies `/api/*` to `http://127.0.0.1:8765`
- Hot Module Replacement is enabled

**Important:** The backend must be running, otherwise API calls will fail.

## Build

```cmd
npm run build
```

Output goes to `dist/`. The build is a static SPA that can be served by any HTTP server.

## Preview the Production Build

```cmd
npm run preview
```

Serves the `dist/` folder on a local port.

## Lint

```cmd
npm run lint
```

Uses ESLint (from the Vite React-TS template).

## Tech Stack

| Category | Library |
|---|---|
| Framework | React 18 |
| Language | TypeScript 5 |
| Build | Vite |
| Styling | Tailwind CSS v4 |
| Theming | CSS custom properties + `data-theme` |
| UI primitives | Radix UI |
| Icons | Lucide React |
| Toast | Sonner |
| State (server) | TanStack Query |
| State (UI) | Zustand + persist |
| Routing | React Router v6 |
| Forms | Native + controlled components |
| i18n | i18next + react-i18next |
| Table | Custom (with TanStack Table patterns) |
| Animations | CSS keyframes + Tailwind utilities |

## Environment

The frontend talks to `/api/*` on the same origin. In development, Vite proxies those requests to the backend. In production (packaged app), the same origin rule applies.

**No environment variables are needed.** Everything is configured through `vite.config.ts`.

## Theming

Themes are defined in `src/styles/themes.css` as CSS custom properties:

```css
:root[data-theme="indigo-light"] {
  --color-primary: 79 70 229;
  --color-surface: 255 255 255;
  /* ... */
}
```

Values are **space-separated RGB** so opacity modifiers work:

```tsx
style={{ color: 'rgb(var(--color-primary) / 0.5)' }}
```

Theme is applied before React mounts via an inline script in `index.html` to prevent FOUC.

**To add a new theme:**

1. Add a `[data-theme="my-theme"]` block in `src/styles/themes.css`
2. Register it in `THEMES` in `src/features/settings/settingsStore.ts`
3. Add the theme card text in `i18n/fa.ts` and `i18n/en.ts` (if needed)

No other changes are required.

## Internationalization (i18n)

Add keys to both `src/i18n/fa.ts` and `src/i18n/en.ts`:

```ts
// fa.ts
export default {
  translation: {
    myFeature: { title: 'عنوان من' },
  },
}
```

Then use in components:

```tsx
const { t } = useTranslation()
<h1>{t('myFeature.title')}</h1>
```

**RTL handling:**

- The app sets `dir="rtl"` on `<html>` when Persian is selected.
- Use logical Tailwind properties: `ms-*`, `me-*`, `ps-*`, `pe-*` (not `ml-*`).
- To force a direction on a specific component, use `dir="ltr"` locally.

## Path Aliases

The Vite config defines `@` as `src/`:

```ts
import { Button } from '@/components/ui/button'
```

Works in both TypeScript and Vite.

## API Client

All API calls go through `src/api/client.ts`, which:

- Sets `baseURL: '/api'`
- Normalizes backend errors into `Error` with a readable `message`
- Has a 60-second timeout (to accommodate slow LLM calls)

Endpoints are grouped in `src/api/*.ts`:

| File | Domain |
|---|---|
| `projects.ts` | Project CRUD |
| `sources.ts` | Source upload / list / update / delete |
| `glossary.ts` | Glossary entry CRUD |
| `process.ts` | Start / cancel pipeline + SSE URL |
| `export.ts` | Export download URLs |
| `settings.ts` | Key/value settings + user stopwords |
| `llm.ts` | LLM provider list + config + test |

## State Management Strategy

| State | Tool | Reason |
|---|---|---|
| Server data | TanStack Query | Caching, invalidation, refetch |
| App preferences | Zustand + persist | Survives reload (theme, language) |
| Transient UI | React `useState` | Local to component |
| Cross-component dialog | Zustand + Promise | `useConfirm()` returns a Promise |
| Live progress | Custom hook + `EventSource` | SSE streaming |

## Progress Streaming (SSE)

The `useProgressStream` hook:

1. Opens an `EventSource` on `/api/process/{id}/events`
2. Replays history first (last 100 events), then receives live events
3. Auto-closes when a terminal event (`done`, `error`, `cancelled`) is received

The `ProgressLog` component:

- Auto-scrolls **only the container**, not the whole page
- Detects user scroll-up and pauses auto-scroll
- Shows a "Latest" button to jump to the bottom

## Adding a UI Primitive

1. Create `src/components/ui/my-component.tsx`
2. Use `React.forwardRef` and export a typed component
3. Merge class names with `cn()` from `@/lib/utils`
4. Prefer headless (Radix) primitives and control styling at the call site

## Animations

Standard animations live in `src/index.css`:

| Class | Effect |
|---|---|
| `rg-anim-fade-in` | Fade (250ms) |
| `rg-anim-fade-up` | Fade + 4px rise |
| `rg-anim-scale-fade` | Fade + 0.97 → 1 scale |
| `rg-stagger` | Staggered children |
| `rg-skeleton` | Shimmer loading placeholder |

Duration tokens: `--anim-fast: 120ms`, `--anim-normal: 250ms`.

Respects `prefers-reduced-motion`.

## Theming Details

**Palette per theme:**

- `--color-bg`, `--color-surface`, `--color-surface-alt`
- `--color-border`, `--color-text`, `--color-text-muted`
- `--color-primary`, `--color-primary-hover`, `--color-primary-fg`
- `--color-success`, `--color-warning`, `--color-error`, `--color-info`

**Contrast notes:**

- Light themes use amber-500 for warning (not amber-600) so `cancelled` is visually distinct from `failed` (which uses `--color-error`).
- Dark themes use amber-400.

## Build for Production

```cmd
npm run build
```

The `dist/` folder contains:

- `index.html` — with the FOUC-prevention script inline
- `assets/` — hashed JS and CSS bundles
- `vite.svg` — favicon

To serve: point any static server (Nginx, Caddy, or `pywebview`) at `dist/`.

## Packaging (Future)

When bundled with the desktop launcher:

1. `npm run build` produces `dist/`
2. `pywebview` loads `dist/index.html`
3. The FastAPI backend runs on `127.0.0.1:8765`
4. `pywebview` serves the SPA and proxies `/api` to the backend (or the SPA uses absolute URLs)

## Troubleshooting

### `Failed to resolve import "@/..."`

- Check `vite.config.ts` — the `@` alias must be defined.
- Restart Vite and clear the cache:
  ```cmd
  Remove-Item -Recurse -Force node_modules\.vite
  npm run dev
  ```

### Vite says "Port 5173 is already in use"

Kill the existing process:

```powershell
Get-Process node | Stop-Process -Force
```

### CSS changes not visible

Hard refresh: `Ctrl+Shift+R`.

### RTL layout is broken

- Check `document.documentElement.dir` in DevTools.
- Ensure the component uses logical properties (`ms-*`, `me-*`), not `ml-*`.

### Toast notifications appear in the wrong corner

The `Toaster` component in `App.tsx` positions based on `language`:

- Persian → `bottom-left`
- English → `bottom-right`

## Further Reading

- [../README.md](../README.md) — Project overview
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — System architecture
- [../docs/DEVELOPER_GUIDE.md](../docs/DEVELOPER_GUIDE.md) — Development guide
- [../docs/USER_GUIDE.md](../docs/USER_GUIDE.md) — End-user guide (Persian)

## License

MIT — see [../LICENSE](../LICENSE).