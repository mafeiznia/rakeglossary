import { useTranslation } from 'react-i18next'
import { BookOpen } from 'lucide-react'
import { LanguageToggle } from './LanguageToggle'
import { ThemeToggle } from './ThemeToggle'

export function Header() {
  const { t } = useTranslation()

  return (
    <header
      className="h-16 border-b flex items-center justify-between px-6"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      <div className="flex items-center gap-3">
        <BookOpen
          className="h-6 w-6"
          style={{ color: 'rgb(var(--color-primary))' }}
        />
        <div>
          <h1 className="text-lg font-semibold leading-tight">
            {t('app.name')}
          </h1>
          <p
            className="text-xs"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {t('app.tagline')}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <ThemeToggle />
        <LanguageToggle />
      </div>
    </header>
  )
}