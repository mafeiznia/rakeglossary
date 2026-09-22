import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

export const Dialog = DialogPrimitive.Root
export const DialogTrigger = DialogPrimitive.Trigger
export const DialogPortal = DialogPrimitive.Portal
export const DialogClose = DialogPrimitive.Close

export const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      'fixed inset-0 z-50',
      'data-[state=open]:animate-[rg-fade-in_250ms_cubic-bezier(0.16,1,0.3,1)_both]',
      'data-[state=closed]:animate-[rg-fade-in_200ms_cubic-bezier(0.16,1,0.3,1)_reverse_both]',
      className
    )}
    style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    {...props}
  />
))
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
        'w-full max-w-lg rounded-lg border p-6 shadow-lg',
        'data-[state=open]:animate-[rg-scale-fade_250ms_cubic-bezier(0.16,1,0.3,1)_both]',
        'data-[state=closed]:animate-[rg-scale-fade_200ms_cubic-bezier(0.16,1,0.3,1)_reverse_both]',
        'max-h-[90vh] overflow-y-auto',
        className
      )}
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
        color: 'rgb(var(--color-text))',
      }}
      {...props}
    >
      {children}
      <DialogPrimitive.Close
        className="absolute end-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-[rgb(var(--color-primary))]"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
))
DialogContent.displayName = DialogPrimitive.Content.displayName

export function DialogHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col space-y-1.5 mb-4', className)}
      {...props}
    />
  )
}

export function DialogFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 gap-2 mt-6',
        className
      )}
      {...props}
    />
  )
}

export const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn('text-lg font-semibold leading-none', className)}
    {...props}
  />
))
DialogTitle.displayName = DialogPrimitive.Title.displayName

export const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn('text-sm', className)}
    style={{ color: 'rgb(var(--color-text-muted))' }}
    {...props}
  />
))
DialogDescription.displayName = DialogPrimitive.Description.displayName