import * as React from 'react'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'

// ============================================================
// TooltipProvider
// ------------------------------------------------------------
// Wrap the entire app with this provider once.
// Controls global delay.
// ============================================================

interface TooltipProviderProps {
  children: React.ReactNode
  delayDuration?: number
  skipDelayDuration?: number
}

export function TooltipProvider({
  children,
  delayDuration = 300,
  skipDelayDuration = 100,
}: TooltipProviderProps) {
  return (
    <TooltipPrimitive.Provider
      delayDuration={delayDuration}
      skipDelayDuration={skipDelayDuration}
    >
      {children}
    </TooltipPrimitive.Provider>
  )
}

// ============================================================
// Tooltip
// ------------------------------------------------------------
// Simple wrapper: <Tooltip content="..."><el/></Tooltip>.
// If no content, children are returned as-is.
// ============================================================

interface TooltipProps {
  /** Tooltip content. If empty/undefined, no tooltip is shown. */
  content?: React.ReactNode
  /** The element that triggers the tooltip. */
  children: React.ReactNode
  /** Preferred side. Defaults to "top". */
  side?: 'top' | 'right' | 'bottom' | 'left'
  /** Alignment along the side. Defaults to "center". */
  align?: 'start' | 'center' | 'end'
  /** Optional max width for long tooltips. */
  maxWidth?: number
}

export function Tooltip({
  content,
  children,
  side = 'top',
  align = 'center',
  maxWidth = 320,
}: TooltipProps) {
  // If there is no content, skip the whole Radix machinery
  if (content === undefined || content === null || content === '') {
    return <>{children}</>
  }

  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side={side}
          align={align}
          sideOffset={6}
          collisionPadding={8}
          style={{
            zIndex: 50,
            backgroundColor: '#1e293b',
            color: '#f1f5f9',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            lineHeight: 1.6,
            boxShadow:
              '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
            maxWidth,
            wordBreak: 'break-word',
            animation: 'tooltip-in 120ms ease-out',
          }}
        >
          {content}
          <TooltipPrimitive.Arrow
            width={10}
            height={5}
            style={{ fill: '#1e293b' }}
          />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  )
}