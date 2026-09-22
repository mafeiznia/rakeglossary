import { Palette } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { THEMES, useSettings } from '@/features/settings/settingsStore'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { theme, setTheme } = useSettings()
  const { i18n } = useTranslation()
  const isFa = i18n.language === 'fa'

  // Cycle through themes with a single click
  const idx = THEMES.findIndex((t) => t.value === theme)
  const next = THEMES[(idx + 1) % THEMES.length]

  return (
    <Button
      variant="ghost"
      size="icon"
      title={
        isFa ? `تم بعدی: ${next.labelFa}` : `Next theme: ${next.label}`
      }
      onClick={() => setTheme(next.value)}
    >
      <Palette className="h-5 w-5" />
    </Button>
  )
}