import { useEffect, useRef, useState } from 'react'
import { ArrowDown, CheckCircle2, AlertCircle, Loader2, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ProgressEvent } from '@/types'
import { cn } from '@/lib/utils'

interface Props {
  events: ProgressEvent[]
  connected: boolean
}

const ICONS = {
  info: Info,
  success: CheckCircle2,
  warning: AlertCircle,
  error: AlertCircle,
}

const COLORS = {
  info: 'rgb(var(--color-info))',
  success: 'rgb(var(--color-success))',
  warning: 'rgb(var(--color-warning))',
  error: 'rgb(var(--color-error))',
}

// Distance (in px) from bottom below which we consider the user "at bottom"
const AT_BOTTOM_THRESHOLD = 40

export function ProgressLog({ events, connected }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Detect user scroll: enable/disable auto-scroll
  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const distanceFromBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight
    const isAtBottom = distanceFromBottom <= AT_BOTTOM_THRESHOLD
    setAutoScroll(isAtBottom)
    setShowScrollButton(!isAtBottom)
  }

  // Auto-scroll (only the container, not the page) when new events arrive
  useEffect(() => {
    if (!autoScroll) return
    const el = containerRef.current
    if (!el) return
    // Use scrollTop — only affects the container, not the whole page
    el.scrollTop = el.scrollHeight
  }, [events.length, autoScroll])

  // When log first opens, jump to bottom
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [])

  const scrollToBottom = () => {
    const el = containerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
    setAutoScroll(true)
    setShowScrollButton(false)
  }

  return (
    <div
      className="rounded-lg border overflow-hidden relative"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-2 border-b flex items-center justify-between"
        style={{ borderColor: 'rgb(var(--color-border))' }}
      >
        <h3 className="text-sm font-semibold">Progress</h3>
        <div className="flex items-center gap-3">
          <span
            className="text-xs"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {events.length} event{events.length !== 1 ? 's' : ''}
          </span>
          {connected && (
            <span
              className="flex items-center gap-1 text-xs"
              style={{ color: 'rgb(var(--color-info))' }}
            >
              <Loader2 className="h-3 w-3 animate-spin" />
              live
            </span>
          )}
        </div>
      </div>

      {/* Log container — this is the scrollable area */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="p-3 max-h-[320px] overflow-y-auto space-y-1 font-mono text-xs"
        dir="ltr"
      >
        {events.length === 0 && (
          <p style={{ color: 'rgb(var(--color-text-muted))' }}>
            No events yet...
          </p>
        )}

        {events.map((ev, i) => {
          const Icon = ICONS[ev.level] || Info
          const color = COLORS[ev.level] || COLORS.info
          return (
            <div
              key={i}
              className="flex items-start gap-2 rg-anim-fade-up"
            >
              <Icon
                className="h-3.5 w-3.5 mt-0.5 shrink-0"
                style={{ color }}
              />
              <div className="flex-1 min-w-0">
                <span className={cn('break-words')}>{ev.message}</span>
                {ev.current > 0 && ev.total > 0 && (
                  <span
                    className="ms-2"
                    style={{ color: 'rgb(var(--color-text-muted))' }}
                  >
                    [{ev.current}/{ev.total}]
                  </span>
                )}
              </div>
              <span
                className="shrink-0"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {ev.step}
              </span>
            </div>
          )
        })}
      </div>

      {/* Floating "scroll to bottom" button */}
      {showScrollButton && (
        <div className="absolute bottom-3 end-3 z-10">
          <Button
            size="sm"
            onClick={scrollToBottom}
            className="shadow-lg"
          >
            <ArrowDown className="h-3.5 w-3.5" />
            Latest
          </Button>
        </div>
      )}
    </div>
  )
}