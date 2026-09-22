/**
 * Tests for the useAbout hook.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Mock the API layer BEFORE importing the hook
vi.mock('@/api/about', () => ({
  fetchAbout: vi.fn(),
}))

import { fetchAbout } from '@/api/about'
import { useAbout } from '@/hooks/useAbout'
import type { AboutResponse } from '@/types/about'

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

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useAbout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns data from fetchAbout on success', async () => {
    vi.mocked(fetchAbout).mockResolvedValueOnce(mockAbout)

    const { result } = renderHook(() => useAbout(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockAbout)
    expect(fetchAbout).toHaveBeenCalledTimes(1)
  })

  it('exposes error when fetchAbout rejects', async () => {
    vi.mocked(fetchAbout).mockRejectedValueOnce(new Error('boom'))

    const { result } = renderHook(() => useAbout(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeInstanceOf(Error)
    expect((result.current.error as Error).message).toBe('boom')
  })
})