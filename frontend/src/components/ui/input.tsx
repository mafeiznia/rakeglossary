import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-10 w-full rounded-md border px-3 py-2 text-sm',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
        'disabled:cursor-not-allowed disabled:opacity-50',
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
Input.displayName = 'Input'