import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface EmptyStateProps {
  /** Lucide icon component to display. */
  icon: LucideIcon
  /** Main title (short, bold). */
  title: string
  /** Optional subtitle/description. */
  description?: string
  /** Optional action button label. */
  actionLabel?: string
  /**
   * Optional action handler. If provided (and actionHref is not),
   * the action renders as a <button>.
   */
  onAction?: () => void
  /**
   * Optional href for a Link-style action. If provided, the action
   * renders as a real <Link> (proper semantics, supports Ctrl+Click).
   * Takes precedence over onAction.
   */
  actionHref?: string
  /** Visual size: default is "page" (large), "compact" for panels. */
  size?: 'page' | 'compact'
  /** Additional class names. */
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionHref,
  size = 'page',
  className,
}: EmptyStateProps) {
  const isCompact = size === 'compact'

  // Decide how to render the action, if any
  const hasAction = Boolean(actionLabel && (actionHref || onAction))

  return (
    <div
      className={cn(
        'rounded-lg border text-center flex flex-col items-center justify-center',
        isCompact ? 'p-8 gap-3' : 'p-16 gap-4',
        'rg-stagger',
        className
      )}
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      {/* Icon */}
      <Icon
        className={cn('shrink-0', isCompact ? 'h-8 w-8' : 'h-12 w-12')}
        style={{ color: 'rgb(var(--color-text-muted))' }}
      />

      {/* Title + description */}
      <div className={cn(isCompact ? 'space-y-1' : 'space-y-2')}>
        <h3
          className={cn(
            'font-semibold',
            isCompact ? 'text-sm' : 'text-base'
          )}
          style={{ color: 'rgb(var(--color-text))' }}
        >
          {title}
        </h3>

        {description && (
          <p
            className={cn(
              'max-w-md mx-auto',
              isCompact ? 'text-xs' : 'text-sm'
            )}
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {description}
          </p>
        )}
      </div>

      {/* Action */}
      {hasAction && (
        <>
          {actionHref ? (
            <Link to={actionHref}>
              <Button size={isCompact ? 'sm' : 'default'}>
                {actionLabel}
              </Button>
            </Link>
          ) : (
            <Button
              onClick={onAction}
              size={isCompact ? 'sm' : 'default'}
            >
              {actionLabel}
            </Button>
          )}
        </>
      )}
    </div>
  )
}