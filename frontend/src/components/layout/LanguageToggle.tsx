import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useSettings } from '@/features/settings/settingsStore'
import { Button } from '@/components/ui/button'

export function LanguageToggle() {
  const { toggleLanguage } = useSettings()
  const { i18n } = useTranslation()

  const handleClick = () => {
    toggleLanguage()
    const next = i18n.language === 'fa' ? 'en' : 'fa'
    i18n.changeLanguage(next)
  }

  return (
    <Button variant="ghost" size="icon" title="Language" onClick={handleClick}>
      <Languages className="h-5 w-5" />
      <span className="sr-only">Switch language</span>
    </Button>
  )
}