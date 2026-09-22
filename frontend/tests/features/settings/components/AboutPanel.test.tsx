/**
 * Tests for the AboutPanel component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { AboutResponse } from '@/types/about'

// Mock the hook directly
vi.mock('@/hooks/useAbout', () => ({
  useAbout: vi.fn(),
}))

// Mock react-i18next — t() returns the key, i18n.language controls direction
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'fa' },
  }),
}))

import { useAbout } from '@/hooks/useAbout'
import { AboutPanel } from '@/features/settings/components/AboutPanel'

const mockAbout: AboutResponse = {
  app_name: 'RakeGlossary',
  version: '0.1.0',
  tagline_fa: 'تولیدکننده خودکار واژه‌نامه',
  tagline_en: 'Automated glossary generator',
  license: 'MIT',
  copyright_year: 2026,
  author: {
    name_fa: 'محمود اهرپور فیض‌نیا',
    name_en: 'Mahmoud Aharpour Feiznia',
    role_fa: 'طراحی و توسعه',
    role_en: 'Designed & Developed by',
    email: 'ma.feiznia@gmail.com',
    linkedin: 'https://www.linkedin.com/in/example',
    website: 'https://www.yadoto.ir',
  },
  tech_stack: {
    frontend: 'React 18 + Vite + Tailwind',
    backend: 'FastAPI + Uvicorn',
    python: '3.12.2',
    database: 'SQLite',
    nlp: 'spaCy + RAKE + YAKE',
  },
  github: 'https://github.com/mafeiznia/rakeglossary',
}

function mockQuery(data: AboutResponse | undefined) {
  vi.mocked(useAbout).mockReturnValue({
    data,
    isLoading: !data,
    isSuccess: !!data,
    isError: false,
    error: null,
  } as ReturnType<typeof useAbout>)
}

describe('AboutPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state when data is undefined', () => {
    mockQuery(undefined)
    render(<AboutPanel />)
    expect(screen.getByText('about.loading')).toBeInTheDocument()
  })

  it('renders app name and version', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)
    expect(screen.getByText('RakeGlossary')).toBeInTheDocument()
    // Version appears as "about.versionLabel 0.1.0" (rendered inline)
    expect(screen.getByText(/0\.1\.0/)).toBeInTheDocument()
  })

  it('renders both Persian and English author names (fa mode)', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)
    expect(screen.getByText('محمود اهرپور فیض‌نیا')).toBeInTheDocument()
    expect(screen.getByText('Mahmoud Aharpour Feiznia')).toBeInTheDocument()
  })

  it('renders contact links with correct href attributes', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)

    const emailLink = screen.getByRole('link', { name: /ma\.feiznia@gmail\.com/ })
    expect(emailLink).toHaveAttribute('href', 'mailto:ma.feiznia@gmail.com')

    const linkedinLink = screen.getByRole('link', { name: /LinkedIn/ })
    expect(linkedinLink).toHaveAttribute('href', mockAbout.author.linkedin)
    expect(linkedinLink).toHaveAttribute('target', '_blank')
    expect(linkedinLink).toHaveAttribute('rel', 'noreferrer')

    const websiteLink = screen.getByRole('link', { name: /yadoto\.ir/ })
    expect(websiteLink).toHaveAttribute('href', mockAbout.author.website)
    expect(websiteLink).toHaveAttribute('target', '_blank')
  })

  it('renders tech stack values', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)
    expect(screen.getByText('React 18 + Vite + Tailwind')).toBeInTheDocument()
    expect(screen.getByText('FastAPI + Uvicorn')).toBeInTheDocument()
    expect(screen.getByText('3.12.2')).toBeInTheDocument()
    expect(screen.getByText('SQLite')).toBeInTheDocument()
    expect(screen.getByText('spaCy + RAKE + YAKE')).toBeInTheDocument()
  })

  it('renders license and copyright line', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)
    expect(screen.getByText('MIT License')).toBeInTheDocument()
    expect(
      screen.getByText(/© 2026 Mahmoud Aharpour Feiznia/)
    ).toBeInTheDocument()
  })

  it('renders GitHub link when github field is present', () => {
    mockQuery(mockAbout)
    render(<AboutPanel />)
    const githubLink = screen.getByRole('link', { name: /about\.sourceCode/ })
    expect(githubLink).toHaveAttribute('href', mockAbout.github)
  })

  it('does not render GitHub link when github field is empty', () => {
    mockQuery({ ...mockAbout, github: '' })
    render(<AboutPanel />)
    expect(
      screen.queryByRole('link', { name: /about\.sourceCode/ })
    ).not.toBeInTheDocument()
  })
})