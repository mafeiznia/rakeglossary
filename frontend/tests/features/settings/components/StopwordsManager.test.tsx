/**
 * Tests for StopwordsManager.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'

const mockAdd = vi.fn()
const mockRemove = vi.fn()
const mockUseStopwords = vi.fn()
vi.mock('@/features/settings/hooks/useStopwords', () => ({
  useStopwords: () => mockUseStopwords(),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
  }),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <button {...rest}>{children}</button>
  ),
}))
vi.mock('@/components/ui/input', () => ({
  Input: (props: Record<string, unknown>) => <input {...props} />,
}))
vi.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
    </div>
  ),
}))

import { StopwordsManager } from '@/features/settings/components/StopwordsManager'

function defaultHook(overrides: Record<string, unknown> = {}) {
  return {
    words: [],
    total: 0,
    isLoading: false,
    add: mockAdd,
    remove: mockRemove,
    isAdding: false,
    isRemoving: false,
    ...overrides,
  }
}

describe('StopwordsManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAdd.mockResolvedValue(undefined)
    mockRemove.mockResolvedValue(undefined)
  })

  it('renders title and hint', () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    render(<StopwordsManager />)
    expect(screen.getByText('settings.blacklist')).toBeInTheDocument()
    expect(screen.getByText('settings.blacklistHint')).toBeInTheDocument()
  })

  it('add button is disabled when draft is empty', () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    render(<StopwordsManager />)
    const btn = screen.getByText('settings.blacklistAdd').closest('button')
    expect(btn).toBeDisabled()
  })

  it('add button is enabled when draft has text', async () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    const user = userEvent.setup()
    render(<StopwordsManager />)
    const input = screen.getByPlaceholderText('settings.blacklistPlaceholder')
    await user.type(input, 'hello')
    const btn = screen.getByText('settings.blacklistAdd').closest('button')
    expect(btn).not.toBeDisabled()
  })

  it('rejects Persian characters and shows error, keeps draft empty', () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    render(<StopwordsManager />)
    const input = screen.getByPlaceholderText(
      'settings.blacklistPlaceholder'
    ) as HTMLInputElement

    fireEvent.change(input, { target: { value: 'کتاب' } })

    expect(input.value).toBe('')
    expect(
      screen.getByText('settings.blacklistEnglishOnly')
    ).toBeInTheDocument()
  })

  it('calls add with trimmed word and clears input', async () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    const user = userEvent.setup()
    render(<StopwordsManager />)
    const input = screen.getByPlaceholderText(
      'settings.blacklistPlaceholder'
    ) as HTMLInputElement
    await user.type(input, '  hello  ')
    await user.click(screen.getByText('settings.blacklistAdd'))

    expect(mockAdd).toHaveBeenCalledWith('hello')
    expect(input.value).toBe('')
  })

  it('pressing Enter triggers add', async () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    const user = userEvent.setup()
    render(<StopwordsManager />)
    await user.type(
      screen.getByPlaceholderText('settings.blacklistPlaceholder'),
      'term{Enter}'
    )
    expect(mockAdd).toHaveBeenCalledWith('term')
  })

  it('input and button are disabled while isAdding', () => {
    mockUseStopwords.mockReturnValue(defaultHook({ isAdding: true }))
    render(<StopwordsManager />)
    expect(
      screen.getByPlaceholderText('settings.blacklistPlaceholder')
    ).toBeDisabled()
    expect(
      screen.getByText('settings.blacklistAdd').closest('button')
    ).toBeDisabled()
  })

  it('shows loading indicator when isLoading', () => {
    mockUseStopwords.mockReturnValue(defaultHook({ isLoading: true }))
    render(<StopwordsManager />)
    expect(screen.getByText('common.loading')).toBeInTheDocument()
  })

  it('shows EmptyState when total is 0', () => {
    mockUseStopwords.mockReturnValue(defaultHook())
    render(<StopwordsManager />)
    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    expect(
      screen.getByText('settings.blacklistEmptyTitle')
    ).toBeInTheDocument()
  })

  it('renders chips and count when words exist', () => {
    mockUseStopwords.mockReturnValue(
      defaultHook({ words: ['alpha', 'beta'], total: 2 })
    )
    render(<StopwordsManager />)
    expect(screen.getByText('alpha')).toBeInTheDocument()
    expect(screen.getByText('beta')).toBeInTheDocument()
    expect(
      screen.getByText(/settings\.blacklistCount:.*"count":2/)
    ).toBeInTheDocument()
  })

  it('remove calls remove with the word', async () => {
    mockUseStopwords.mockReturnValue(
      defaultHook({ words: ['alpha'], total: 1 })
    )
    const user = userEvent.setup()
    render(<StopwordsManager />)
    await user.click(screen.getByTitle('common.delete'))
    expect(mockRemove).toHaveBeenCalledWith('alpha')
  })
})