/**
 * Tests for useProgressStream hook.
 *
 * The streamProgress API is mocked; we control when events are emitted and
 * verify the hook state transitions.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

// --- Mock streamProgress ---
type StreamCallbacks = {
  onEvent: (e: unknown) => void
  onOpen?: () => void
  onError?: () => void
}
const mockStream = {
  close: vi.fn(),
}
let capturedCallbacks: StreamCallbacks | null = null
vi.mock('@/api/progress', () => ({
  streamProgress: (
    _id: string,
    onEvent: (e: unknown) => void,
    _onError: () => void,
    onClose: () => void
  ) => {
    capturedCallbacks = { onEvent, onError: onClose }
    return mockStream
  },
}))

import { useProgressStream } from '@/features/progress/hooks/useProgressStream'

describe('useProgressStream', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    capturedCallbacks = null
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not open a stream when isLive is false', () => {
    const { result } = renderHook(() =>
      useProgressStream('proj-1', false)
    )
    expect(capturedCallbacks).toBeNull()
    expect(result.current.connected).toBe(false)
    expect(result.current.events).toEqual([])
  })

  it('does not open a stream when projectId is undefined', () => {
    const { result } = renderHook(() =>
      useProgressStream(undefined, true)
    )
    expect(capturedCallbacks).toBeNull()
    expect(result.current.connected).toBe(false)
  })

  it('opens stream and sets connected=true when isLive', () => {
    const { result } = renderHook(() =>
      useProgressStream('proj-1', true)
    )
    expect(capturedCallbacks).not.toBeNull()
    expect(result.current.connected).toBe(true)
  })

  it('appends events as they arrive', () => {
    const { result } = renderHook(() =>
      useProgressStream('proj-1', true)
    )

    act(() => {
      capturedCallbacks?.onEvent({
        level: 'info',
        message: 'first',
        step: 'keywords',
        current: 1,
        total: 5,
      })
      capturedCallbacks?.onEvent({
        level: 'info',
        message: 'second',
        step: 'keywords',
        current: 2,
        total: 5,
      })
    })

    expect(result.current.events).toHaveLength(2)
    expect(result.current.latest?.message).toBe('second')
  })

  it('closes stream 300ms after a "done" event and disconnects', () => {
    const { result } = renderHook(() =>
      useProgressStream('proj-1', true)
    )

    act(() => {
      capturedCallbacks?.onEvent({
        level: 'success',
        message: 'finished',
        step: 'done',
        current: 1,
        total: 1,
      })
    })

    // Still connected right away
    expect(mockStream.close).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(300)
    })

    expect(mockStream.close).toHaveBeenCalledTimes(1)
    expect(result.current.connected).toBe(false)
  })

  it('closes stream 300ms after an "error" event', () => {
    renderHook(() => useProgressStream('proj-1', true))

    act(() => {
      capturedCallbacks?.onEvent({
        level: 'error',
        message: 'boom',
        step: 'error',
        current: 1,
        total: 1,
      })
      vi.advanceTimersByTime(300)
    })

    expect(mockStream.close).toHaveBeenCalledTimes(1)
  })

  it('closes stream 300ms after a "cancelled" event', () => {
    renderHook(() => useProgressStream('proj-1', true))

    act(() => {
      capturedCallbacks?.onEvent({
        level: 'warning',
        message: 'cancelled by user',
        step: 'cancelled',
        current: 1,
        total: 1,
      })
      vi.advanceTimersByTime(300)
    })

    expect(mockStream.close).toHaveBeenCalledTimes(1)
  })

  it('closes stream when isLive switches to false', () => {
    const { rerender, result } = renderHook(
      ({ live }: { live: boolean }) => useProgressStream('proj-1', live),
      { initialProps: { live: true } }
    )

    expect(result.current.connected).toBe(true)

    rerender({ live: false })

    expect(mockStream.close).toHaveBeenCalled()
    expect(result.current.connected).toBe(false)
  })

  it('cleans up on unmount', () => {
    const { unmount } = renderHook(() =>
      useProgressStream('proj-1', true)
    )
    unmount()
    expect(mockStream.close).toHaveBeenCalledTimes(1)
  })
})