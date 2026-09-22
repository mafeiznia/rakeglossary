/**
 * Tests for GlossaryTable.
 *
 * Focus areas:
 *  - Empty state when no entries
 *  - Row rendering (term, persian, context, score, freq, source)
 *  - Inline editing (EditableCell): click → edit → save with Enter
 *  - Cancel with Escape
 *  - onDelete / onBlacklist callbacks
 *  - AI badges (pos, category, note, alternatives)
 *  - Untranslated marker
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

import { GlossaryTable } from '@/features/glossary/components/GlossaryTable'

type Entry = {
  id: number
  english_term: string
  persian_term: string
  persian_definition: string
  english_definition: string
  context: string
  source: string
  score: number
  frequency: number
  pos?: string | null
  category?: string | null
  translator_note?: string | null
  persian_alternatives?: string[] | null
  persian_transliteration?: string | null
}

function makeEntry(overrides: Partial<Entry> = {}): Entry {
  return {
    id: 1,
    english_term: 'alpha',
    persian_term: 'آلفا',
    persian_definition: 'تعریف آلفا',
    english_definition: '',
    context: 'The alpha particle...',
    source: 'Wikipedia',
    score: 0.42,
    frequency: 7,
    pos: null,
    category: null,
    translator_note: null,
    persian_alternatives: null,
    persian_transliteration: null,
    ...overrides,
  }
}

function defaultProps(entries: Entry[] = [makeEntry()]) {
  return {
    entries: entries as never,
    onUpdate: vi.fn().mockResolvedValue(undefined),
    onDelete: vi.fn().mockResolvedValue(undefined),
    onBlacklist: vi.fn().mockResolvedValue(undefined),
  }
}

describe('GlossaryTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders empty state when entries is empty', () => {
    render(<GlossaryTable {...(defaultProps([]) as never)} />)
    expect(screen.getByText('No glossary entries')).toBeInTheDocument()
  })

  it('renders all table headers', () => {
    render(<GlossaryTable {...(defaultProps() as never)} />)
    expect(screen.getByText('English Term')).toBeInTheDocument()
    expect(screen.getByText('Persian Term')).toBeInTheDocument()
    expect(screen.getByText('Persian Definition')).toBeInTheDocument()
    expect(screen.getByText('Score ⓘ')).toBeInTheDocument()
    expect(screen.getByText('Freq ⓘ')).toBeInTheDocument()
    expect(screen.getByText('Source ⓘ')).toBeInTheDocument()
  })

  it('renders row values correctly', () => {
    render(<GlossaryTable {...(defaultProps() as never)} />)
    expect(screen.getByText('alpha')).toBeInTheDocument()
    expect(screen.getByText('آلفا')).toBeInTheDocument()
    expect(screen.getByText('تعریف آلفا')).toBeInTheDocument()
    expect(screen.getByText('Wikipedia')).toBeInTheDocument()
    expect(screen.getByText('0.420')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('renders context in quotes', () => {
    render(<GlossaryTable {...(defaultProps() as never)} />)
    expect(screen.getByText('"The alpha particle..."')).toBeInTheDocument()
  })

  it('renders em-dash when context is missing', () => {
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry({ context: '' })]) as never)}
      />
    )
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  // --- Inline editing ---

  it('enters edit mode when cell is clicked', async () => {
    const user = userEvent.setup()
    render(<GlossaryTable {...(defaultProps() as never)} />)

    await user.click(screen.getByText('آلفا'))
    const input = screen.getByDisplayValue('آلفا')
    expect(input).toBeInTheDocument()
  })

  it('calls onUpdate when edit is saved with Enter', async () => {
    const onUpdate = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry()]) as never)}
        onUpdate={onUpdate}
      />
    )

    await user.click(screen.getByText('آلفا'))
    const input = screen.getByDisplayValue('آلفا')
    await user.clear(input)
    await user.type(input, 'آلفای جدید{Enter}')

    expect(onUpdate).toHaveBeenCalledWith(1, { persian_term: 'آلفای جدید' })
  })

  it('cancels edit with Escape', async () => {
    const onUpdate = vi.fn()
    const user = userEvent.setup()
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry()]) as never)}
        onUpdate={onUpdate}
      />
    )

    await user.click(screen.getByText('آلفا'))
    const input = screen.getByDisplayValue('آلفا')
    await user.clear(input)
    await user.type(input, 'changed{Escape}')

    expect(onUpdate).not.toHaveBeenCalled()
    expect(screen.getByText('آلفا')).toBeInTheDocument()
  })

  it('does not call onUpdate when value is unchanged', async () => {
    const onUpdate = vi.fn()
    const user = userEvent.setup()
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry()]) as never)}
        onUpdate={onUpdate}
      />
    )

    await user.click(screen.getByText('آلفا'))
    const input = screen.getByDisplayValue('آلفا')
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onUpdate).not.toHaveBeenCalled()
  })

  // --- Action buttons ---
  // NOTE: `title` and `Tooltip` content are not accessible via getByTitle
  // because the mock for Tooltip drops the title. We locate buttons by
  // their lucide icon class instead.

  it('calls onDelete with entry id when delete button is clicked', async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    const { container } = render(
      <GlossaryTable
        {...(defaultProps([makeEntry({ id: 99 })]) as never)}
        onDelete={onDelete}
      />
    )

    const deleteBtn = container
      .querySelector('.lucide-trash-2')
      ?.closest('button') as HTMLButtonElement
    expect(deleteBtn).toBeTruthy()
    await user.click(deleteBtn)
    expect(onDelete).toHaveBeenCalledWith(99)
  })

  it('calls onBlacklist with term and id', async () => {
    const onBlacklist = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    const { container } = render(
      <GlossaryTable
        {...(defaultProps([
          makeEntry({ id: 99, english_term: 'zeta' }),
        ]) as never)}
        onBlacklist={onBlacklist}
      />
    )

    const blacklistBtn = container
      .querySelector('.lucide-ban')
      ?.closest('button') as HTMLButtonElement
    expect(blacklistBtn).toBeTruthy()
    await user.click(blacklistBtn)
    expect(onBlacklist).toHaveBeenCalledWith('zeta', 99)
  })

  it('does not render blacklist button when onBlacklist is undefined', () => {
    const props = defaultProps()
    delete (props as { onBlacklist?: unknown }).onBlacklist
    const { container } = render(<GlossaryTable {...(props as never)} />)
    expect(container.querySelector('.lucide-ban')).not.toBeInTheDocument()
  })

  // --- Untranslated marker ---

  it('shows untranslated marker when persian_term is empty', () => {
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry({ persian_term: '' })]) as never)}
      />
    )
    expect(screen.getByText('(ترجمه نشده)')).toBeInTheDocument()
  })

  // --- AI extras ---

  it('renders pos badge when present', () => {
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry({ pos: 'NOUN' })]) as never)}
      />
    )
    expect(screen.getByText('NOUN')).toBeInTheDocument()
  })

  it('renders category badge when present', () => {
    render(
      <GlossaryTable
        {...(defaultProps([makeEntry({ category: 'physics' })]) as never)}
      />
    )
    expect(screen.getByText('physics')).toBeInTheDocument()
  })

  it('renders translator note icon when note present', () => {
    const { container } = render(
      <GlossaryTable
        {...(defaultProps([
          makeEntry({ translator_note: 'note here' }),
        ]) as never)}
      />
    )
    expect(container.querySelector('.lucide-info')).toBeInTheDocument()
  })

  it('renders alternatives indicator when alternatives present', () => {
    render(
      <GlossaryTable
        {...(defaultProps([
          makeEntry({ persian_alternatives: ['a', 'b'] }),
        ]) as never)}
      />
    )
    expect(screen.getByText('+2 alternatives')).toBeInTheDocument()
  })

  it('renders transliteration when present', () => {
    const { container } = render(
      <GlossaryTable
        {...(defaultProps([
          makeEntry({ persian_transliteration: 'alpha' }),
        ]) as never)}
      />
    )
    // transliteration is rendered in a <div dir="ltr"> with italic styling
    const transliteration = container.querySelector(
      'div.text-\\[10px\\].italic'
    )
    expect(transliteration).toBeInTheDocument()
    expect(transliteration?.textContent).toBe('alpha')
  })
})