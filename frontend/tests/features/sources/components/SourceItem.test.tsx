/**
 * Tests for SourceItem.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
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
vi.mock('@/components/ui/switch', () => ({
  Switch: ({
    checked,
    onCheckedChange,
    disabled,
  }: {
    checked: boolean
    onCheckedChange: (v: boolean) => void
    disabled?: boolean
  }) => (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onCheckedChange(!checked)}
    >
      {checked ? 'on' : 'off'}
    </button>
  ),
}))

import { SourceItem } from '@/features/sources/components/SourceItem'

function makeSource(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    source_type: 'file' as const,
    original_name: 'book.pdf',
    word_count: 1234,
    included: true,
    ...overrides,
  }
}

function defaultProps(overrides: Record<string, unknown> = {}) {
  return {
    source: makeSource(),
    onToggleIncluded: vi.fn().mockResolvedValue(undefined),
    onRename: vi.fn().mockResolvedValue(undefined),
    onDelete: vi.fn().mockResolvedValue(undefined),
    isUpdating: false,
    isRemoving: false,
    ...overrides,
  }
}

describe('SourceItem', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders name, type and word count', () => {
    render(<SourceItem {...(defaultProps() as never)} />)
    expect(screen.getByText('book.pdf')).toBeInTheDocument()
    expect(screen.getByText('file')).toBeInTheDocument()
    expect(screen.getByText(/1,234 words/)).toBeInTheDocument()
  })

  it('renders uppercase source type', () => {
    render(<SourceItem {...(defaultProps() as never)} />)
    expect(screen.getByText('file')).toHaveClass('uppercase')
  })

  it('enters edit mode when pencil button is clicked', async () => {
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps() as never)} />)

    await user.click(screen.getByTitle('common.edit'))

    const input = screen.getByDisplayValue('book.pdf')
    expect(input).toBeInTheDocument()
  })

  it('renames via Enter key', async () => {
    const onRename = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onRename }) as never)} />)

    await user.click(screen.getByTitle('common.edit'))
    const input = screen.getByDisplayValue('book.pdf')
    await user.clear(input)
    await user.type(input, 'new.pdf{Enter}')

    expect(onRename).toHaveBeenCalledWith('new.pdf')
  })

  it('cancels edit via Escape key', async () => {
    const onRename = vi.fn()
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onRename }) as never)} />)

    await user.click(screen.getByTitle('common.edit'))
    const input = screen.getByDisplayValue('book.pdf')
    await user.clear(input)
    await user.type(input, 'changed{Escape}')

    expect(onRename).not.toHaveBeenCalled()
    expect(screen.getByText('book.pdf')).toBeInTheDocument()
  })

  it('does not call onRename when name is empty', async () => {
    const onRename = vi.fn()
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onRename }) as never)} />)

    await user.click(screen.getByTitle('common.edit'))
    const input = screen.getByDisplayValue('book.pdf')
    await user.clear(input)
    await user.type(input, '{Enter}')

    expect(onRename).not.toHaveBeenCalled()
  })

  it('does not call onRename when name unchanged', async () => {
    const onRename = vi.fn()
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onRename }) as never)} />)

    await user.click(screen.getByTitle('common.edit'))
    const input = screen.getByDisplayValue('book.pdf')
    await user.type(input, '{Enter}')

    expect(onRename).not.toHaveBeenCalled()
  })

  it('toggles included via switch', async () => {
    const onToggleIncluded = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(
      <SourceItem {...(defaultProps({ onToggleIncluded }) as never)} />
    )

    await user.click(screen.getByRole('switch'))

    expect(onToggleIncluded).toHaveBeenCalledWith(false)
  })

  it('calls onDelete when window.confirm returns true', async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onDelete }) as never)} />)

    await user.click(screen.getByTitle('common.delete'))

    expect(window.confirm).toHaveBeenCalledTimes(1)
    expect(onDelete).toHaveBeenCalledTimes(1)
  })

  it('does not call onDelete when window.confirm returns false', async () => {
    const onDelete = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    const user = userEvent.setup()
    render(<SourceItem {...(defaultProps({ onDelete }) as never)} />)

    await user.click(screen.getByTitle('common.delete'))

    expect(onDelete).not.toHaveBeenCalled()
  })

  it('disables switch and delete button while isUpdating / isRemoving', () => {
    render(
      <SourceItem
        {...(defaultProps({ isUpdating: true, isRemoving: true }) as never)}
      />
    )
    expect(screen.getByRole('switch')).toBeDisabled()
    expect(screen.getByTitle('common.delete')).toBeDisabled()
  })

  it('uses the file icon for file sources', () => {
    const { container } = render(
      <SourceItem {...(defaultProps() as never)} />
    )
    expect(container.querySelector('.lucide-file-text')).toBeInTheDocument()
  })

  it('uses the type icon for text sources', () => {
    const { container } = render(
      <SourceItem
        {...(defaultProps({
          source: makeSource({ source_type: 'text', original_name: 'Chapter 1' }),
        }) as never)}
      />
    )
    expect(container.querySelector('.lucide-type')).toBeInTheDocument()
  })
})