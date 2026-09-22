import { create } from 'zustand'

export interface ConfirmOptions {
  title?: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'default' | 'destructive'
}

interface ConfirmState {
  open: boolean
  options: ConfirmOptions
  resolver: ((v: boolean) => void) | null
  show: (opts: ConfirmOptions) => Promise<boolean>
  resolve: (v: boolean) => void
  handleOpenChange: (v: boolean) => void
}

export const useConfirmStore = create<ConfirmState>((set, get) => ({
  open: false,
  options: {},
  resolver: null,

  /** Opens the dialog and returns a Promise that resolves to true/false. */
  show: (opts) =>
    new Promise<boolean>((resolve) => {
      set({ open: true, options: opts, resolver: resolve })
    }),

  /** User clicked confirm or cancel. */
  resolve: (v) => {
    const r = get().resolver
    set({ open: false, resolver: null })
    if (r) r(v)
  },

  /** Dialog wants to open/close (e.g., Escape or X button). */
  handleOpenChange: (v) => {
    if (v) return // don't open from outside
    const r = get().resolver
    set({ open: false, resolver: null })
    if (r) r(false)
  },
}))

/** Imperative hook to trigger a confirm dialog. */
export function useConfirm() {
  return useConfirmStore((s) => s.show)
}