/**
 * Integration tests for ProjectsPage.
 *
 * Children (ProjectCard, ProjectCardSkeleton, EmptyState, Button) are mocked
 * where they have their own concerns, so this suite focuses on page logic:
 *  - loading / error / empty / populated states
 *  - header count
 *  - delete flow (confirm → remove → toast)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'

// --- Mock the projects list hook ---
const mockRemove = vi.fn()
const mockUseProjectsList = vi.fn()
vi.mock('@/features/projects/hooks/useProjectsList', () => ({
  useProjectsList: () => mockUseProjectsList(),
}))

// --- Mock confirm ---
const mockConfirm = vi.fn()
vi.mock('@/features/confirm/confirmStore', () => ({
  useConfirm: () => mockConfirm,
}))

// --- Mock toast ---
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// --- Mock react-i18next ---
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      if (params) {
        return `${key}:${JSON.stringify(params)}`
      }
      return key
    },
  }),
}))

// --- Mock ProjectCard to render identifiable markers ---
vi.mock('@/features/projects/components/ProjectCard', () => ({
  ProjectCard: ({
    project,
    onDelete,
    isDeleting,
  }: {
    project: { id: string; title: string }
    onDelete: (id: string) => void
    isDeleting: boolean
  }) => (
    <div data-testid="project-card">
      <span>{project.title}</span>
      <button onClick={() => onDelete(project.id)}>
        delete-{project.title}
      </button>
      {isDeleting && <span data-testid="deleting" />}
    </div>
  ),
}))

vi.mock('@/features/projects/components/ProjectCardSkeleton', () => ({
  ProjectCardSkeleton: () => <div data-testid="project-card-skeleton" />,
}))

// --- Mock EmptyState ---
vi.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
    </div>
  ),
}))

// --- Mock Button to a plain <button> so we don't need full Radix setup ---
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...rest }: { children: ReactNode }) => (
    <button {...rest}>{children}</button>
  ),
}))

import { toast } from 'sonner'
import { ProjectsPage } from '@/pages/ProjectsPage'

// --- Sample data ---
const sampleProjects = {
  items: [
    {
      id: 'proj-1',
      title: 'Book One',
      status: 'done',
      source_count: 2,
      entry_count: 50,
    },
    {
      id: 'proj-2',
      title: 'Book Two',
      status: 'processing',
      source_count: 1,
      entry_count: 0,
    },
  ],
  total: 2,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ProjectsPage />
    </MemoryRouter>
  )
}

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockConfirm.mockResolvedValue(true)
    mockRemove.mockResolvedValue(undefined)
  })

  // --- Header ---

  it('renders the page title', () => {
    mockUseProjectsList.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(screen.getByText('projects.title')).toBeInTheDocument()
  })

  it('shows count in subtitle when total > 0', () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(
      screen.getByText(/projects\.countLabel:.*"count":2/)
    ).toBeInTheDocument()
  })

  it('shows subtitle when total = 0', () => {
    mockUseProjectsList.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(screen.getByText('projects.subtitle')).toBeInTheDocument()
  })

  // --- Loading / error / empty ---

  it('renders 6 skeletons during loading', () => {
    mockUseProjectsList.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(screen.getAllByTestId('project-card-skeleton')).toHaveLength(6)
  })

  it('renders error message on error', () => {
    mockUseProjectsList.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('boom'),
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(screen.getByText(/Error: boom/)).toBeInTheDocument()
  })

  it('renders empty state when there are no projects', () => {
    mockUseProjectsList.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    expect(screen.getByText('projects.empty')).toBeInTheDocument()
  })

  it('renders a ProjectCard for each project', () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    renderPage()
    const cards = screen.getAllByTestId('project-card')
    expect(cards).toHaveLength(2)
    expect(screen.getByText('Book One')).toBeInTheDocument()
    expect(screen.getByText('Book Two')).toBeInTheDocument()
  })

  // --- Delete flow ---

  it('shows confirm dialog and deletes when user confirms', async () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    mockConfirm.mockResolvedValueOnce(true)
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('delete-Book One'))

    expect(mockConfirm).toHaveBeenCalledTimes(1)
    const confirmArgs = mockConfirm.mock.calls[0][0]
    expect(confirmArgs.title).toBe('confirm.deleteProject.title')
    expect(confirmArgs.variant).toBe('destructive')

    await waitFor(() => {
      expect(mockRemove).toHaveBeenCalledWith('proj-1')
    })
    expect(toast.success).toHaveBeenCalledWith('toast.projectDeleted')
  })

  it('does nothing when user cancels the confirm dialog', async () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    mockConfirm.mockResolvedValueOnce(false)
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('delete-Book One'))

    expect(mockConfirm).toHaveBeenCalledTimes(1)
    expect(mockRemove).not.toHaveBeenCalled()
    expect(toast.success).not.toHaveBeenCalled()
  })

  it('shows error toast when remove rejects', async () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: false,
    })
    mockConfirm.mockResolvedValueOnce(true)
    mockRemove.mockRejectedValueOnce(new Error('network down'))
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('delete-Book One'))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('network down')
    })
    expect(toast.success).not.toHaveBeenCalled()
  })

  it('passes isDeleting flag down to ProjectCard', () => {
    mockUseProjectsList.mockReturnValue({
      data: sampleProjects,
      isLoading: false,
      isError: false,
      error: null,
      remove: mockRemove,
      isDeleting: true,
    })
    renderPage()
    expect(screen.getAllByTestId('deleting')).toHaveLength(2)
  })
})