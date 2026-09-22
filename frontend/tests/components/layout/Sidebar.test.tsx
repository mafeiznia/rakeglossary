/**
 * Tests for the Sidebar component, especially the version badge.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { AboutResponse } from '@/types/about'

vi.mock('@/hooks/useAbout', () => ({
  useAbout: vi.fn(),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'fa' },
  }),
}))

import { useAbout } from '@/hooks/useAbout'
import { Sidebar } from '@/components/layout/Sidebar'

const mockAbout: AboutResponse = {
  app_name: 'RakeGlossary',
  version: '0.1.0',
  tagline_fa: '',
  tagline_en: '',
  license: 'MIT',
  copyright_year: 2026,
  author: {
    name_fa: '',
    name_en: '',
    role_fa: '',
    role_en: '',
    email: '',
    linkedin: '',
    website: '',
  },
  tech_stack: {
    frontend: '',
    backend: '',
    python: '',
    database: '',
    nlp: '',
  },
  github: '',
}

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>
  )
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders navigation items', () => {
    vi.mocked(useAbout).mockReturnValue({
      data: mockAbout,
    } as ReturnType<typeof useAbout>)

    renderSidebar()
    expect(screen.getByText('nav.home')).toBeInTheDocument()
    expect(screen.getByText('nav.projects')).toBeInTheDocument()
    expect(screen.getByText('nav.settings')).toBeInTheDocument()
  })

  it('shows version badge with correct version', () => {
    vi.mocked(useAbout).mockReturnValue({
      data: mockAbout,
    } as ReturnType<typeof useAbout>)

    renderSidebar()
    expect(screen.getByText('v0.1.0')).toBeInTheDocument()
  })

  it('shows fallback version when about data is not yet loaded', () => {
    vi.mocked(useAbout).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useAbout>)

    renderSidebar()
    expect(screen.getByText('v0.0.0')).toBeInTheDocument()
  })

  it('version badge has tooltip with translated label', () => {
    vi.mocked(useAbout).mockReturnValue({
      data: mockAbout,
    } as ReturnType<typeof useAbout>)

    renderSidebar()
    const badge = screen.getByText('v0.1.0')
    expect(badge).toHaveAttribute('title', 'about.version_tooltip')
  })
})