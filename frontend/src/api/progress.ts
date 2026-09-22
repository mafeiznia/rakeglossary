import type { ProgressEvent } from '@/types'

export interface ProgressStream {
  close: () => void
}

export function streamProgress(
  projectId: string,
  onEvent: (event: ProgressEvent) => void,
  onError: (err: Event) => void,
  onClose: () => void
): ProgressStream {
  const url = `/api/process/${projectId}/events`
  const source = new EventSource(url)

  source.addEventListener('progress', (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as ProgressEvent
      onEvent(data)
    } catch {
      // ignore malformed events
    }
  })

  source.addEventListener('error', onError)

  source.addEventListener('open', () => {
    // connected
  })

  // EventSource doesn't have a direct "close" event, but we can track
  // when the server closes the stream by listening to error with readyState CLOSED
  const originalOnError = onError

  source.addEventListener('error', (ev) => {
    if (source.readyState === EventSource.CLOSED) {
      onClose()
    } else {
      originalOnError(ev)
    }
  })

  return {
    close: () => source.close(),
  }
}