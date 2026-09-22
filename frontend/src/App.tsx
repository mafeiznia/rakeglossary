import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Toaster } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { HomePage } from '@/pages/HomePage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { ProjectDetailPage } from '@/pages/ProjectDetailPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { ConfirmHost } from '@/features/confirm/ConfirmHost'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useSettings } from '@/features/settings/settingsStore'

function App() {
  const { theme, language } = useSettings()
  const { i18n } = useTranslation()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    document.documentElement.setAttribute(
      'dir',
      language === 'fa' ? 'rtl' : 'ltr'
    )
    document.documentElement.setAttribute('lang', language)
    i18n.changeLanguage(language)
  }, [language, i18n])

  return (
    <TooltipProvider>
      <Toaster
        position={language === 'fa' ? 'bottom-left' : 'bottom-right'}
        richColors
        closeButton
        toastOptions={{
          style: {
            backgroundColor: 'rgb(var(--color-surface))',
            color: 'rgb(var(--color-text))',
            border: '1px solid rgb(var(--color-border))',
          },
        }}
      />
      <ConfirmHost />
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:id" element={<ProjectDetailPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  )
}

export default App