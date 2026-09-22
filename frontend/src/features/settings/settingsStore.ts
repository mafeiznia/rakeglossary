import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeName =
  | 'indigo-light'
  | 'emerald-light'
  | 'rose-light'
  | 'slate-dark'
  | 'midnight-dark'

export type Language = 'fa' | 'en'

interface SettingsState {
  theme: ThemeName
  language: Language
  setTheme: (t: ThemeName) => void
  setLanguage: (l: Language) => void
  toggleLanguage: () => void
}

export const useSettings = create<SettingsState>()(
  persist(
    (set, get) => ({
      theme: 'indigo-light',
      language: 'fa',
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
      toggleLanguage: () =>
        set({ language: get().language === 'fa' ? 'en' : 'fa' }),
    }),
    { name: 'rakeglossary-settings' }
  )
)

export const THEMES: { value: ThemeName; label: string; labelFa: string }[] = [
  { value: 'indigo-light', label: 'Indigo Light', labelFa: 'ایندیگو روشن' },
  { value: 'emerald-light', label: 'Emerald Light', labelFa: 'زمرد روشن' },
  { value: 'rose-light', label: 'Rose Light', labelFa: 'رز روشن' },
  { value: 'slate-dark', label: 'Slate Dark', labelFa: 'اسلیت تاریک' },
  { value: 'midnight-dark', label: 'Midnight Dark', labelFa: 'نیمه‌شب' },
]