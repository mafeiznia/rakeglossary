import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { THEMES, useSettings } from '@/features/settings/settingsStore'
import { StopwordsManager } from '@/features/settings/components/StopwordsManager'
import { LlmSettings } from '@/features/settings/components/LlmSettings'
import { AboutPanel } from '@/features/settings/components/AboutPanel'

export function SettingsPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { theme, setTheme, language, setLanguage } = useSettings()
  const [lastProjectId, setLastProjectId] = useState<string | null>(null)

  // Read last visited project from localStorage
  useEffect(() => {
    try {
      const id = localStorage.getItem('lastProjectId')
      if (id) setLastProjectId(id)
    } catch {
      // ignore
    }
  }, [])

  const handleLanguage = (lang: 'fa' | 'en') => {
    setLanguage(lang)
    i18n.changeLanguage(lang)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header with back-to-project button */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-bold">{t('settings.title')}</h2>
        {lastProjectId && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/projects/${lastProjectId}`)}
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            {t('settings.backToProject')}
          </Button>
        )}
      </div>

      {/* Appearance */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">{t('settings.appearance')}</h3>

        <div>
          <label className="block text-sm font-medium mb-1">
            {t('settings.theme')}
          </label>
          <p
            className="text-xs mb-3"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {t('settings.themeHint')}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {THEMES.map((th) => (
              <button
                key={th.value}
                onClick={() => setTheme(th.value)}
                className="rounded-lg border-2 p-3 text-start transition-all"
                style={{
                  backgroundColor: 'rgb(var(--color-surface))',
                  borderColor:
                    theme === th.value
                      ? 'rgb(var(--color-primary))'
                      : 'rgb(var(--color-border))',
                }}
              >
                <div className="text-sm font-medium">
                  {language === 'fa' ? th.labelFa : th.label}
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Language */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">{t('settings.language')}</h3>
        <p
          className="text-xs"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          {t('settings.languageHint')}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => handleLanguage('fa')}
            className="rounded-md border-2 px-4 py-2 text-sm transition-all"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor:
                language === 'fa'
                  ? 'rgb(var(--color-primary))'
                  : 'rgb(var(--color-border))',
            }}
          >
            {t('settings.persian')}
          </button>
          <button
            onClick={() => handleLanguage('en')}
            className="rounded-md border-2 px-4 py-2 text-sm transition-all"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor:
                language === 'en'
                  ? 'rgb(var(--color-primary))'
                  : 'rgb(var(--color-border))',
            }}
          >
            {t('settings.english')}
          </button>
        </div>
      </section>

      {/* LLM */}
      <LlmSettings />

      {/* Stopwords / Blacklist */}
      <StopwordsManager />

      {/* About */}
      <AboutPanel />
    </div>
  )
}