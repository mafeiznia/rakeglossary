/**
 * Integration tests for SourcesPanel.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'

// --- useSources mock ---
let mockHook: Record<string, unknown>
vi.mock('@/features/sources/hooks/useSources', () => ({
  useSources: () => mockHook,
}))

// --- useConfirm ---
const mockConfirm = vi.fn()
vi.mock('@/features/confirm/confirmStore', () => ({
  useConfirm: () => mockConfirm,
}))

// --- toast ---
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// --- i18n ---
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
  }),
}))

// --- UI primitives ---
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <button {...rest}>{children}</button>
  ),
}))
vi.mock('@/components/ui/input', () => ({
  Input: (props: Record<string, unknown>) => <input {...props} />,
}))
vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <label {...rest}>{children}</label>
  ),
}))
vi.mock('@/components/ui/textarea', () => ({
  Textarea: (props: Record<string, unknown>) => <textarea {...props} />,
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
      {actionLabel && <button onClick={onAction}>{actionLabel}</button>}
    </div>
  ),
}))

// --- Child components ---
vi.mock('@/features/sources/components/MultiFileDropzone', () => ({
  MultiFileDropzone: ({ onFiles }: { onFiles: (f: File[]) => void }) => (
    <div data-testid="dropzone">
      <button onClick={() => onFiles([new File(['x'], 'a.pdf')])}>
        fake-upload
      </button>
    </div>
  ),
}))

vi.mock('@/features/sources/components/SourceItem', () => ({
  SourceItem: ({
    source,
    onDelete,
  }: {
    source: { id: number; original_name: string }
    onDelete: () => Promise<void>
  }) => (
    <div data-testid={`source-${source.id}`}>
      <span>{source.original_name}</span>
      <button onClick={() => onDelete()}>delete-{source.id}</button>
    </div>
  ),
}))

import { toast } from 'sonner'
import { SourcesPanel } from '@/features/sources/components/SourcesPanel'

const sampleSources = [
  {
    id: 1,
    source_type: 'file',
    original_name: 'a.pdf',
    word_count: 100,
    included: true,
  },
  {
    id: 2,
    source_type: 'text',
    original_name: 'Chapter 1',
    word_count: 50,
    included: false,
  },
]

function makeHook(overrides: Record<string, unknown> = {}) {
  return {
    sources: [],
    isLoading: false,
    upload: vi.fn().mockResolvedValue(undefined),
    addText: vi.fn().mockResolvedValue(undefined),
    update: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
    isUploading: false,
    isAddingText: false,
    isUpdating: false,
    isRemoving: false,
    ...overrides,
  }
}

describe('SourcesPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockHook = makeHook()
    mockConfirm.mockResolvedValue(true)
  })

  it('renders title and total/included counts', () => {
    mockHook = makeHook({ sources: sampleSources })
    render(<SourcesPanel projectId="proj-1" />)
    expect(screen.getByText('sources.title')).toBeInTheDocument()
    expect(screen.getByText('2 sources.totalLabel · 1 sources.activeLabel'))
      .toBeInTheDocument()
  })

  it('shows loading text while fetching', () => {
    mockHook = makeHook({ isLoading: true })
    render(<SourcesPanel projectId="proj-1" />)
    expect(screen.getByText('common.loading')).toBeInTheDocument()
  })

  it('shows EmptyState when no sources', () => {
    mockHook = makeHook({ sources: [] })
    render(<SourcesPanel projectId="proj-1" />)
    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    expect(screen.getByText('sources.emptyTitle')).toBeInTheDocument()
  })

  it('opens add panel when Add button is clicked', async () => {
    mockHook = makeHook({ sources: sampleSources })
    const user = userEvent.setup()
    render(<SourcesPanel projectId="proj-1" />)

    await user.click(screen.getByText('sources.addButton'))
    expect(screen.getByTestId('dropzone')).toBeInTheDocument()
  })

  it('renders a SourceItem for each source', () => {
    mockHook = makeHook({ sources: sampleSources })
    render(<SourcesPanel projectId="proj-1" />)
    expect(screen.getByTestId('source-1')).toBeInTheDocument()
    expect(screen.getByTestId('source-2')).toBeInTheDocument()
  })

  it('calls upload when dropzone provides files and shows success', async () => {
    const upload = vi.fn().mockResolvedValue(undefined)
    mockHook = makeHook({ sources: sampleSources, upload })
    const user = userEvent.setup()
    render(<SourcesPanel projectId="proj-1" />)

    await user.click(screen.getByText('sources.addButton'))
    await user.click(screen.getByText('fake-upload'))

    await waitFor(() => {
      expect(upload).toHaveBeenCalledTimes(1)
      expect(toast.success).toHaveBeenCalled()
    })
  })

  it('delete flow: confirm true → remove + toast.success', async () => {
    const remove = vi.fn().mockResolvedValue(undefined)
    mockHook = makeHook({ sources: sampleSources, remove })
    mockConfirm.mockResolvedValueOnce(true)
    const user = userEvent.setup()
    render(<SourcesPanel projectId="proj-1" />)

    await user.click(screen.getByText('delete-1'))

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalledTimes(1)
      expect(remove).toHaveBeenCalledWith(1)
      expect(toast.success).toHaveBeenCalledWith('toast.sourceDeleted')
    })
  })

  it('delete flow: confirm false → no remove', async () => {
    const remove = vi.fn()
    mockHook = makeHook({ sources: sampleSources, remove })
    mockConfirm.mockResolvedValueOnce(false)
    const user = userEvent.setup()
    render(<SourcesPanel projectId="proj-1" />)

    await user.click(screen.getByText('delete-1'))

    expect(mockConfirm).toHaveBeenCalledTimes(1)
    expect(remove).not.toHaveBeenCalled()
  })
})