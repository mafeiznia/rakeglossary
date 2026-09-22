/**
 * Integration tests for the SettingsPage.
 *
 * Child components (StopwordsManager, LlmSettings, AboutPanel) are mocked
 * because they have their own dedicated test suites.
 * The test verifies:
 *  - Title rendering
 *  - localStorage-driven "back to project" button
 *  - Navigation on button click
 *  - Theme selection
 *  - Language selection
 *  - Child sections mounting
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// --- Mock child components to isolate SettingsPage ---
vi.mock('@/features/settings/components/StopwordsManager', () => ({
  StopwordsManager: () => <div data-testid="stopwords-manager" />,
}))
vi.mock('@/features/settings/components/LlmSettings', () => ({
  LlmSettings: () => <div data-testid="llm-settings" />,
}))
vi.mock('@/features/settings/components/AboutPanel', () => ({
  AboutPanel: () => <div data-testid="about-panel" />,
}))

// --- Mock react-router-dom's useNavigate ---
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// --- Mock react-i18next ---
const mockChangeLanguage = vi.fn()
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { changeLanguage: mockChangeLanguage },
  }),
}))

// --- Mock the settings store ---
const mockSetTheme = vi.fn()
const mockSetLanguage = vi.fn()
vi.mock('@/features/settings/settingsStore', () => ({
  useSettings: () => ({
    theme: 'indigo-light',
    language: 'fa',
    setTheme: mockSetTheme,
    setLanguage: mockSetLanguage,
  }),
  THEMES: [
    { value: 'indigo-light', label: 'Indigo Light', labelFa: 'تم روشن' },
    { value: 'emerald-light', label: 'Emerald Light', labelFa: 'تم زمرد' },
  ],
}))

import { SettingsPage } from '@/pages/SettingsPage'

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders the settings title', () => {
    render(<SettingsPage />)
    expect(screen.getByText('settings.title')).toBeInTheDocument()
  })

  it('does not show back-to-project button when no last project', () => {
    render(<SettingsPage />)
    expect(screen.queryByText('settings.backToProject')).not.toBeInTheDocument()
  })

  it('shows back-to-project button when lastProjectId exists', async () => {
    localStorage.setItem('lastProjectId', 'proj-123')
    render(<SettingsPage />)

    await waitFor(() => {
      expect(screen.getByText('settings.backToProject')).toBeInTheDocument()
    })
  })

  it('navigates to last project on button click', async () => {
    localStorage.setItem('lastProjectId', 'proj-123')
    const user = userEvent.setup()
    render(<SettingsPage />)

    await waitFor(() => {
      expect(screen.getByText('settings.backToProject')).toBeInTheDocument()
    })

    await user.click(screen.getByText('settings.backToProject'))
    expect(mockNavigate).toHaveBeenCalledWith('/projects/proj-123')
    expect(mockNavigate).toHaveBeenCalledTimes(1)
  })

  it('renders all theme buttons', () => {
    render(<SettingsPage />)
    expect(screen.getByText('تم روشن')).toBeInTheDocument()
    expect(screen.getByText('تم زمرد')).toBeInTheDocument()
  })

  it('calls setTheme when a theme is clicked', async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    await user.click(screen.getByText('تم زمرد'))
    expect(mockSetTheme).toHaveBeenCalledWith('emerald-light')
    expect(mockSetTheme).toHaveBeenCalledTimes(1)
  })

  it('renders both language buttons', () => {
    render(<SettingsPage />)
    expect(screen.getByText('settings.persian')).toBeInTheDocument()
    expect(screen.getByText('settings.english')).toBeInTheDocument()
  })

  it('switches to Persian and updates i18n', async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    await user.click(screen.getByText('settings.persian'))
    expect(mockSetLanguage).toHaveBeenCalledWith('fa')
    expect(mockChangeLanguage).toHaveBeenCalledWith('fa')
  })

  it('switches to English and updates i18n', async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    await user.click(screen.getByText('settings.english'))
    expect(mockSetLanguage).toHaveBeenCalledWith('en')
    expect(mockChangeLanguage).toHaveBeenCalledWith('en')
  })

  it('renders all child sections', () => {
    render(<SettingsPage />)
    expect(screen.getByTestId('llm-settings')).toBeInTheDocument()
    expect(screen.getByTestId('stopwords-manager')).toBeInTheDocument()
    expect(screen.getByTestId('about-panel')).toBeInTheDocument()
  })
})