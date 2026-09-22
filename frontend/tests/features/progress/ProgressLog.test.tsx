/**
 * Tests for ProgressLog.
 *
 * Focus:
 *  - Empty state ("No events yet...")
 *  - Rendering events with correct icons/levels
 *  - Live indicator
 *  - Event counter
 *  - Scroll-to-bottom button visibility (requires jsdom DOM properties)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <button {...rest}>{children}</button>
  ),
}))

import { ProgressLog } from '@/features/progress/components/ProgressLog'

type Event = {
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
  step: string
  current: number
  total: number
}

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    level: 'info',
    message: 'Doing something',
    step: 'keywords',
    current: 1,
    total: 10,
    ...overrides,
  }
}

describe('ProgressLog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders header with 0 events in empty state', () => {
    render(<ProgressLog events={[]} connected={false} />)
    expect(screen.getByText('Progress')).toBeInTheDocument()
    expect(screen.getByText('0 events')).toBeInTheDocument()
  })

  it('renders "No events yet..." when events list is empty', () => {
    render(<ProgressLog events={[]} connected={false} />)
    expect(screen.getByText('No events yet...')).toBeInTheDocument()
  })

  it('shows correct event count', () => {
    const events = [makeEvent(), makeEvent(), makeEvent()]
    render(<ProgressLog events={events as never} connected={false} />)
    expect(screen.getByText('3 events')).toBeInTheDocument()
  })

  it('shows "1 event" (singular) for a single event', () => {
    render(<ProgressLog events={[makeEvent()] as never} connected={false} />)
    expect(screen.getByText('1 event')).toBeInTheDocument()
  })

  it('shows live indicator when connected', () => {
    render(<ProgressLog events={[makeEvent()] as never} connected={true} />)
    expect(screen.getByText('live')).toBeInTheDocument()
  })

  it('hides live indicator when not connected', () => {
    render(<ProgressLog events={[makeEvent()] as never} connected={false} />)
    expect(screen.queryByText('live')).not.toBeInTheDocument()
  })

  it('renders event message and step', () => {
    render(
      <ProgressLog
        events={[makeEvent({ message: 'hello world', step: 'merge' })] as never}
        connected={false}
      />
    )
    expect(screen.getByText('hello world')).toBeInTheDocument()
    expect(screen.getByText('merge')).toBeInTheDocument()
  })

  it('renders [current/total] when both are positive', () => {
    render(
      <ProgressLog
        events={[makeEvent({ current: 3, total: 7 })] as never}
        connected={false}
      />
    )
    expect(screen.getByText('[3/7]')).toBeInTheDocument()
  })

  it('omits [current/total] when total is 0', () => {
    render(
      <ProgressLog
        events={[makeEvent({ current: 0, total: 0 })] as never}
        connected={false}
      />
    )
    expect(screen.queryByText(/\[\d+\/\d+\]/)).not.toBeInTheDocument()
  })

  it('renders multiple events with different levels', () => {
    const events = [
      makeEvent({ level: 'info', message: 'info-msg' }),
      makeEvent({ level: 'success', message: 'success-msg' }),
      makeEvent({ level: 'warning', message: 'warn-msg' }),
      makeEvent({ level: 'error', message: 'error-msg' }),
    ]
    render(<ProgressLog events={events as never} connected={false} />)
    expect(screen.getByText('info-msg')).toBeInTheDocument()
    expect(screen.getByText('success-msg')).toBeInTheDocument()
    expect(screen.getByText('warn-msg')).toBeInTheDocument()
    expect(screen.getByText('error-msg')).toBeInTheDocument()
  })

  // --- Scroll behavior (jsdom shims) ---

  it('shows "Latest" button after user scrolls away from bottom', () => {
    // jsdom does not lay out elements. We stub scrollHeight/clientHeight
    // on every element so handleScroll can compute a non-zero distance.
    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      get() {
        return 1000
      },
    })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
      configurable: true,
      get() {
        return 200
      },
    })

    render(<ProgressLog events={[makeEvent()] as never} connected={false} />)

    // Find the scrollable container by role (it's the only div with onScroll).
    // We can find it via the "No events yet" sibling; simplest: query all divs
    // and trigger scroll on the one that has the max-h class.
    const container = document.querySelector('[dir="ltr"]') as HTMLElement
    expect(container).toBeTruthy()

    // Simulate scrollTop at the top (far from bottom)
    Object.defineProperty(container, 'scrollTop', {
      configurable: true,
      value: 0,
      writable: true,
    })
    fireEvent.scroll(container)

    expect(screen.getByText('Latest')).toBeInTheDocument()
  })

  it('hides "Latest" button when at bottom', () => {
    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      get() {
        return 1000
      },
    })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
      configurable: true,
      get() {
        return 200
      },
    })

    render(<ProgressLog events={[makeEvent()] as never} connected={false} />)
    const container = document.querySelector('[dir="ltr"]') as HTMLElement

    Object.defineProperty(container, 'scrollTop', {
      configurable: true,
      value: 800, // scrollHeight - scrollTop - clientHeight = 0
      writable: true,
    })
    fireEvent.scroll(container)

    expect(screen.queryByText('Latest')).not.toBeInTheDocument()
  })

  it('clicking "Latest" hides the button', async () => {
    Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
      configurable: true,
      get() {
        return 1000
      },
    })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
      configurable: true,
      get() {
        return 200
      },
    })

    const user = userEvent.setup()
    render(<ProgressLog events={[makeEvent()] as never} connected={false} />)
    const container = document.querySelector('[dir="ltr"]') as HTMLElement
    Object.defineProperty(container, 'scrollTop', {
      configurable: true,
      value: 0,
      writable: true,
    })
    fireEvent.scroll(container)

    await user.click(screen.getByText('Latest'))
    expect(screen.queryByText('Latest')).not.toBeInTheDocument()
  })
})