import { useEffect, useRef, useState } from 'react'
import { streamProgress } from '@/api/progress'
import type { ProgressEvent } from '@/types'

export function useProgressStream(
  projectId: string | undefined,
  isLive: boolean
) {
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [connected, setConnected] = useState(false)
  const streamRef = useRef<{ close: () => void } | null>(null)

  useEffect(() => {
    if (!projectId || !isLive) {
      // If not live, close any existing stream
      if (streamRef.current) {
        streamRef.current.close()
        streamRef.current = null
      }
      setConnected(false)
      return
    }

    // Reset events on every new "live" session
    setEvents([])
    setConnected(false)

    const stream = streamProgress(
      projectId,
      (event) => {
        setEvents((prev) => [...prev, event])
        if (event.step === 'done' || event.step === 'error' || event.step === 'cancelled') {
          setTimeout(() => {
            stream.close()
            setConnected(false)
          }, 300)
        }
      },
      () => {
        /* EventSource retries automatically */
      },
      () => {
        setConnected(false)
      }
    )

    streamRef.current = stream
    setConnected(true)

    return () => {
      stream.close()
      streamRef.current = null
    }
  }, [projectId, isLive])

  const latest = events.length > 0 ? events[events.length - 1] : null

  return { events, latest, connected }
}