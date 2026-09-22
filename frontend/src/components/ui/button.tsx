import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md',
    'text-sm font-medium',
    // Smooth color transition
    'transition-[background-color,border-color,color,box-shadow,transform]',
    'duration-150 ease-out',
    // Pressed feedback
    'active:scale-[0.98]',
    // Focus ring
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'focus-visible:ring-[rgb(var(--color-primary))]',
    'focus-visible:ring-offset-[rgb(var(--color-bg))]',
    'disabled:pointer-events-none disabled:opacity-50 disabled:active:scale-100',
  ].join(' '),
  {
    variants: {
      variant: {
        default: [
          'bg-[rgb(var(--color-primary))]',
          'text-[rgb(var(--color-primary-fg))]',
          'hover:bg-[rgb(var(--color-primary-hover))]',
        ].join(' '),
        destructive: [
          'bg-[rgb(var(--color-error))]',
          'text-[rgb(var(--color-primary-fg))]',
          'hover:opacity-90',
        ].join(' '),
        outline: [
          'border',
          'bg-[rgb(var(--color-surface))]',
          'text-[rgb(var(--color-text))]',
          'border-[rgb(var(--color-border))]',
          'hover:bg-[rgb(var(--color-surface-alt))]',
        ].join(' '),
        ghost: [
          'text-[rgb(var(--color-text))]',
          'hover:bg-[rgb(var(--color-surface-alt))]',
        ].join(' '),
        link: [
          'text-[rgb(var(--color-primary))]',
          'underline-offset-4',
          'hover:underline',
        ].join(' '),
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
)
Button.displayName = 'Button'

export { buttonVariants }