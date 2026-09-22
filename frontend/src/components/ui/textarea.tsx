import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[120px] w-full rounded-md border px-3 py-2 text-sm',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
        'disabled:cursor-not-allowed disabled:opacity-50 resize-y',
        className
      )}
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
        color: 'rgb(var(--color-text))',
      }}
      {...props}
    />
  )
)
Textarea.displayName = 'Textarea'