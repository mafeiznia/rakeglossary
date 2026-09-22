/**
 * Integration tests for ProjectDetailPage.
 *
 * All children and data hooks are mocked so this suite focuses on:
 *  - loading / error / not-found states
 *  - header rendering (title, status, stats)
 *  - action buttons (Stop / Process / Re-process / Export)
 *  - options panel toggle
 *  - glossary rendering vs empty state
 *  - delete entry / blacklist / metadata flows
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'

// --- Mock react-router-dom (params + navigate) ---
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useParams: () => ({ id: 'proj-1' }),
    useNavigate: () => mockNavigate,
  }
})

// --- Mock react-query client ---
const mockInvalidate = vi.fn()
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>(
    '@tanstack/react-query'
  )
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries: mockInvalidate }),
  }
})

// --- Mock i18n ---
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
  }),
}))

// --- Mock toast ---
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// --- Mock useConfirm ---
const mockConfirm = vi.fn()
vi.mock('@/features/confirm/confirmStore', () => ({
  useConfirm: () => mockConfirm,
}))

// --- Mock data hooks ---
const mockUseProject = vi.fn()
vi.mock('@/features/projects/hooks/useProject', () => ({
  useProject: () => mockUseProject(),
}))

const mockUseGlossary = vi.fn()
vi.mock('@/features/glossary/hooks/useGlossary', () => ({
  useGlossary: () => mockUseGlossary(),
}))

const mockStopwordsAdd = vi.fn()
vi.mock('@/features/settings/hooks/useStopwords', () => ({
  useStopwords: () => ({ add: mockStopwordsAdd }),
}))

const mockUseProgressStream = vi.fn()
vi.mock('@/features/progress/hooks/useProgressStream', () => ({
  useProgressStream: (...args: unknown[]) => mockUseProgressStream(...args),
}))

// --- Mock projects API ---
const mockClearMetadata = vi.fn()
const mockUpdateMetadata = vi.fn()
vi.mock('@/api', () => ({
  projectsApi: {
    clearMetadata: (...args: unknown[]) => mockClearMetadata(...args),
    updateMetadata: (...args: unknown[]) => mockUpdateMetadata(...args),
  },
}))

// --- Mock all child components to render simple markers ---
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    onClick,
    disabled,
    ...rest
  }: {
    children: ReactNode
    onClick?: () => void
    disabled?: boolean
    [k: string]: unknown
  }) => (
    <button onClick={onClick} disabled={disabled} {...rest}>
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}))

vi.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({
    title,
    description,
    actionLabel,
    onAction,
  }: {
    title: string
    description: string
    actionLabel?: string
    onAction?: () => void
  }) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
      {actionLabel && (
        <button onClick={onAction} data-testid="empty-state-action">
          {actionLabel}
        </button>
      )}
    </div>
  ),
}))

vi.mock('@/features/progress/components/ProgressLog', () => ({
  ProgressLog: ({ connected }: { connected: boolean }) => (
    <div data-testid="progress-log" data-connected={String(connected)} />
  ),
}))

vi.mock('@/features/glossary/components/GlossaryTable', () => ({
  GlossaryTable: ({
    entries,
    onDelete,
    onBlacklist,
  }: {
    entries: Array<{ id: number; english_term: string }>
    onDelete: (id: number) => void
    onBlacklist: (term: string, id: number) => void
  }) => (
    <div data-testid="glossary-table">
      {entries.map((e) => (
        <div key={e.id} data-testid={`entry-${e.id}`}>
          <span>{e.english_term}</span>
          <button onClick={() => onDelete(e.id)}>del-{e.id}</button>
          <button onClick={() => onBlacklist(e.english_term, e.id)}>
            blacklist-{e.id}
          </button>
        </div>
      ))}
    </div>
  ),
}))

vi.mock('@/features/glossary/components/GlossaryTableSkeleton', () => ({
  GlossaryTableSkeleton: () => <div data-testid="glossary-skeleton" />,
}))

vi.mock('@/features/projects/components/ExportButtons', () => ({
  ExportButtons: () => <div data-testid="export-buttons" />,
}))

vi.mock('@/features/projects/components/OptionsPanel', () => ({
  OptionsPanel: () => <div data-testid="options-panel" />,
}))

vi.mock('@/features/sources/components/SourcesPanel', () => ({
  SourcesPanel: ({ projectId }: { projectId: string }) => (
    <div data-testid="sources-panel" data-project-id={projectId} />
  ),
}))

vi.mock('@/features/metadata/components/BookMetadataPanel', () => ({
  BookMetadataPanel: ({
    onChange,
  }: {
    onChange: (v: null) => void
  }) => (
    <div data-testid="metadata-panel">
      <button onClick={() => onChange(null)} data-testid="clear-metadata">
        clear-metadata
      </button>
    </div>
  ),
}))

import { toast } from 'sonner'
import { ProjectDetailPage } from '@/pages/ProjectDetailPage'

// --- Fixtures ---
function makeProject(overrides: Record<string, unknown> = {}) {
  return {
    id: 'proj-1',
    title: 'My Book',
    status: 'done',
    num_terms: 500,
    terms_per_1k_words: 15,
    translate_terms: true,
    translate_definitions: true,
    translation_provider: 'argos',
    processing_mode: 'offline',
    use_spacy: true,
    use_rake: true,
    use_yake: true,
    use_ner: true,
    word_count: 12345,
    source_count: 2,
    error_message: null,
    book_metadata: null,
    sources: [
      { id: 1, included: true },
      { id: 2, included: false },
    ],
    ...overrides,
  }
}

function defaultProjectHook(overrides: Record<string, unknown> = {}) {
  return {
    data: makeProject(),
    isLoading: false,
    isError: false,
    error: null,
    reprocess: vi.fn(),
    isReprocessing: false,
    cancel: vi.fn(),
    isCancelling: false,
    ...overrides,
  }
}

function defaultGlossaryHook(overrides: Record<string, unknown> = {}) {
  return {
    data: { entries: [] },
    isLoading: false,
    update: vi.fn(),
    remove: vi.fn(),
    ...overrides,
  }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/projects/proj-1']}>
      <Routes>
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProjectDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockConfirm.mockResolvedValue(true)
    mockUseProgressStream.mockReturnValue({ events: [], connected: false })
    mockStopwordsAdd.mockResolvedValue(undefined)
    mockClearMetadata.mockResolvedValue(undefined)
    mockUpdateMetadata.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // --- Loading / error / not-found ---

  it('renders loading skeleton', () => {
    mockUseProject.mockReturnValue(defaultProjectHook({ data: undefined, isLoading: true }))
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getAllByTestId('skeleton').length).toBeGreaterThan(0)
    expect(screen.getByTestId('glossary-skeleton')).toBeInTheDocument()
  })

  it('renders not-found EmptyState when isError', () => {
    mockUseProject.mockReturnValue(
      defaultProjectHook({ data: undefined, isError: true, error: new Error('nope') })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    expect(screen.getByText('projectDetail.notFoundTitle')).toBeInTheDocument()
  })

  it('auto-navigates to /projects after 5s on error', async () => {
    vi.useFakeTimers()
    mockUseProject.mockReturnValue(
      defaultProjectHook({ data: undefined, isError: true, error: new Error('nope') })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()

    await act(async () => {
      vi.advanceTimersByTime(5000)
    })

    expect(mockNavigate).toHaveBeenCalledWith('/projects', { replace: true })
  })

  // --- Header ---

  it('renders project title, status and stats', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getByText('My Book')).toBeInTheDocument()
    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(screen.getByText(/12,345 words/)).toBeInTheDocument()
    expect(screen.getByText(/2 sources/)).toBeInTheDocument()
    expect(screen.getByText(/500 max terms/)).toBeInTheDocument()
    expect(screen.getByText(/mode: offline/)).toBeInTheDocument()
  })

  it('shows error message banner if project has error_message', () => {
    mockUseProject.mockReturnValue(
      defaultProjectHook({
        data: makeProject({ error_message: 'Something broke' }),
      })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getByText('Something broke')).toBeInTheDocument()
  })

  it('stores project id in localStorage', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(localStorage.getItem('lastProjectId')).toBe('proj-1')
  })

  // --- Processing state ---

  it('shows Stop button and ProgressLog when processing', () => {
    mockUseProject.mockReturnValue(
      defaultProjectHook({ data: makeProject({ status: 'processing' }) })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())
    mockUseProgressStream.mockReturnValue({
      events: [{ id: 1, message: 'busy' }],
      connected: true,
    })

    renderPage()
    expect(screen.getByText('Stop')).toBeInTheDocument()
    expect(screen.getByTestId('progress-log')).toHaveAttribute(
      'data-connected',
      'true'
    )
  })

  it('calls cancel after confirm and shows toast', async () => {
    const mockCancel = vi.fn().mockResolvedValue(undefined)
    mockUseProject.mockReturnValue(
      defaultProjectHook({
        data: makeProject({ status: 'processing' }),
        cancel: mockCancel,
      })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())
    mockConfirm.mockResolvedValueOnce(true)

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('Stop'))

    expect(mockConfirm).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(mockCancel).toHaveBeenCalledTimes(1))
    expect(toast.success).toHaveBeenCalledWith('toast.processingCancelled')
  })

  // --- Actions for non-processing ---

  it('shows Process button and hides ExportButtons when no entries', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getByText('Process')).toBeInTheDocument()
    expect(screen.queryByTestId('export-buttons')).not.toBeInTheDocument()
  })

  it('shows Re-process button and ExportButtons when entries exist', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(
      defaultGlossaryHook({
        data: {
          entries: [
            { id: 1, english_term: 'alpha' },
            { id: 2, english_term: 'beta' },
          ],
        },
      })
    )

    renderPage()
    expect(screen.getByText('Re-process')).toBeInTheDocument()
    expect(screen.getByTestId('export-buttons')).toBeInTheDocument()
  })

  it('disables Process button when no included sources', () => {
    mockUseProject.mockReturnValue(
      defaultProjectHook({
        data: makeProject({
          sources: [{ id: 1, included: false }],
        }),
      })
    )
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    const processBtn = screen.getByText('Process').closest('button')
    expect(processBtn).toBeDisabled()
  })

  // --- Options panel toggle ---

  it('opens OptionsPanel when Process button is clicked', async () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    const user = userEvent.setup()
    renderPage()

    expect(screen.queryByTestId('options-panel')).not.toBeInTheDocument()
    await user.click(screen.getByText('Process'))
    expect(screen.getByTestId('options-panel')).toBeInTheDocument()
    expect(screen.getByText('Start processing')).toBeInTheDocument()
  })

  it('hides OptionsPanel when Cancel is clicked', async () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('Process'))
    expect(screen.getByTestId('options-panel')).toBeInTheDocument()

    await user.click(screen.getByText('Cancel'))
    expect(screen.queryByTestId('options-panel')).not.toBeInTheDocument()
  })

  // --- Children rendered ---

  it('renders BookMetadataPanel, SourcesPanel and empty glossary state', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    renderPage()
    expect(screen.getByTestId('metadata-panel')).toBeInTheDocument()
    expect(screen.getByTestId('sources-panel')).toHaveAttribute(
      'data-project-id',
      'proj-1'
    )
    // Empty state with process-now CTA appears when sources exist but no entries
    expect(screen.getByText('projectDetail.noGlossaryTitle')).toBeInTheDocument()
  })

  it('renders GlossaryTable when entries exist', () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(
      defaultGlossaryHook({
        data: { entries: [{ id: 42, english_term: 'alpha' }] },
      })
    )

    renderPage()
    expect(screen.getByTestId('glossary-table')).toBeInTheDocument()
    expect(screen.getByText('alpha')).toBeInTheDocument()
  })

  // --- Delete entry flow ---

  it('deletes entry after confirm and shows toast', async () => {
    const mockRemove = vi.fn().mockResolvedValue(undefined)
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(
      defaultGlossaryHook({
        data: { entries: [{ id: 42, english_term: 'alpha' }] },
        remove: mockRemove,
      })
    )
    mockConfirm.mockResolvedValueOnce(true)

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('del-42'))

    await waitFor(() => expect(mockRemove).toHaveBeenCalledWith(42))
    expect(toast.success).toHaveBeenCalledWith('toast.entryDeleted')
  })

  it('does not delete entry when confirm is cancelled', async () => {
    const mockRemove = vi.fn()
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(
      defaultGlossaryHook({
        data: { entries: [{ id: 42, english_term: 'alpha' }] },
        remove: mockRemove,
      })
    )
    mockConfirm.mockResolvedValueOnce(false)

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('del-42'))

    expect(mockRemove).not.toHaveBeenCalled()
  })

  // --- Blacklist flow ---

  it('blacklists term and removes entry', async () => {
    const mockRemove = vi.fn().mockResolvedValue(undefined)
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(
      defaultGlossaryHook({
        data: { entries: [{ id: 42, english_term: 'alpha' }] },
        remove: mockRemove,
      })
    )
    mockConfirm.mockResolvedValueOnce(true)

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('blacklist-42'))

    await waitFor(() => {
      expect(mockStopwordsAdd).toHaveBeenCalledWith('alpha')
      expect(mockRemove).toHaveBeenCalledWith(42)
    })
    expect(toast.success).toHaveBeenCalledWith('toast.blacklistAdded')
  })

  // --- Metadata flow ---

  it('clears metadata when BookMetadataPanel requests it', async () => {
    mockUseProject.mockReturnValue(defaultProjectHook())
    mockUseGlossary.mockReturnValue(defaultGlossaryHook())

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByTestId('clear-metadata'))

    await waitFor(() => {
      expect(mockClearMetadata).toHaveBeenCalledWith('proj-1')
      expect(mockInvalidate).toHaveBeenCalledWith({
        queryKey: ['project', 'proj-1'],
      })
    })
    expect(toast.success).toHaveBeenCalledWith('toast.metadataCleared')
  })
})