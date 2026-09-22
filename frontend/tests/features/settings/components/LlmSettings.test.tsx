/**
 * Tests for LlmSettings.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// --- llmApi mock ---
const mockGetProviders = vi.fn()
const mockGetConfig = vi.fn()
const mockUpdateConfig = vi.fn()
const mockTestConfig = vi.fn()
const mockClearConfig = vi.fn()

vi.mock('@/api/llm', () => ({
  llmApi: {
    getProviders: () => mockGetProviders(),
    getConfig: () => mockGetConfig(),
    updateConfig: (payload: unknown) => mockUpdateConfig(payload),
    testConfig: () => mockTestConfig(),
    clearConfig: () => mockClearConfig(),
  },
}))

// --- confirm ---
const mockConfirm = vi.fn()
vi.mock('@/features/confirm/confirmStore', () => ({
  useConfirm: () => mockConfirm,
}))

// --- toast ---
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// --- i18n ---
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
  }),
}))

// --- UI primitives ---
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <button {...rest}>{children}</button>
  ),
}))
vi.mock('@/components/ui/input', () => ({
  Input: (props: Record<string, unknown>) => <input {...props} />,
}))
vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...rest }: { children: ReactNode; [k: string]: unknown }) => (
    <label {...rest}>{children}</label>
  ),
}))
vi.mock('@/components/ui/switch', () => ({
  Switch: ({
    checked,
    onCheckedChange,
  }: {
    checked: boolean
    onCheckedChange: (v: boolean) => void
  }) => (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      data-testid="switch"
    >
      {checked ? 'ON' : 'OFF'}
    </button>
  ),
}))
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

import { toast } from 'sonner'
import { LlmSettings } from '@/features/settings/components/LlmSettings'

const sampleProviders = [
  {
    key: 'openai',
    name: 'OpenAI',
    default_model: 'gpt-4o-mini',
    suggested_models: ['gpt-4o-mini', 'gpt-4o'],
    docs_url: 'https://openai.com/keys',
  },
  {
    key: 'gemini',
    name: 'Gemini',
    default_model: 'gemini-2.0-flash',
    suggested_models: ['gemini-2.0-flash'],
    docs_url: 'https://aistudio.google.com',
  },
]

const sampleConfig = {
  enabled: false,
  provider: 'openai',
  model: 'gpt-4o-mini',
  has_api_key: false,
  api_key_masked: null,
  base_url: null,
}

function renderWithQuery(ui: ReactNode) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('LlmSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetProviders.mockResolvedValue(sampleProviders)
    mockGetConfig.mockResolvedValue(sampleConfig)
    mockConfirm.mockResolvedValue(true)
    mockUpdateConfig.mockResolvedValue({})
    mockTestConfig.mockResolvedValue({
      success: true,
      message: 'pong',
      latency_ms: 42,
    })
    mockClearConfig.mockResolvedValue(undefined)
  })

  it('shows loading indicator while queries are pending', () => {
    mockGetProviders.mockReturnValue(new Promise(() => {}))
    mockGetConfig.mockReturnValue(new Promise(() => {}))
    renderWithQuery(<LlmSettings />)
    expect(screen.getByText('settings.llm.title')).toBeInTheDocument()
    expect(screen.getByText('common.loading')).toBeInTheDocument()
  })

  it('renders title and hint after loading', async () => {
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    expect(screen.getByText('settings.llm.title')).toBeInTheDocument()
  })

  it('hides body when disabled', async () => {
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    expect(
      screen.queryByText(/settings\.llm\.provider/)
    ).not.toBeInTheDocument()
  })

  it('shows body when config.enabled is true', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => {
      expect(screen.getByText(/settings\.llm\.provider/)).toBeInTheDocument()
    })
  })

  it('provider select contains all provider names', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument()
      expect(screen.getByText('Gemini')).toBeInTheDocument()
    })
  })

  it('Save calls updateConfig with current values', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    const user = userEvent.setup()
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('common.save'))

    await waitFor(() => {
      expect(mockUpdateConfig).toHaveBeenCalledTimes(1)
    })
    const payload = mockUpdateConfig.mock.calls[0][0]
    expect(payload.enabled).toBe(true)
    expect(payload.provider).toBe('openai')
    expect(payload.model).toBe('gpt-4o-mini')
  })

  it('Test button is disabled without key and without stored key', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    const testBtn = screen.getByText('settings.llm.test').closest('button')
    expect(testBtn).toBeDisabled()
  })

  it('Test success shows green success message', async () => {
    mockGetConfig.mockResolvedValue({
      ...sampleConfig,
      enabled: true,
      has_api_key: true,
      api_key_masked: 'sk-***abc',
    })
    const user = userEvent.setup()
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('settings.llm.test'))

    await waitFor(() => {
      expect(mockTestConfig).toHaveBeenCalledTimes(1)
      expect(screen.getByText('pong')).toBeInTheDocument()
    })
  })

  it('Test failure renders error message', async () => {
    mockGetConfig.mockResolvedValue({
      ...sampleConfig,
      enabled: true,
      has_api_key: true,
      api_key_masked: 'sk-***abc',
    })
    mockTestConfig.mockResolvedValue({
      success: false,
      message: 'auth failed',
      latency_ms: null,
    })
    const user = userEvent.setup()
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('settings.llm.test'))

    await waitFor(() => {
      expect(screen.getByText('auth failed')).toBeInTheDocument()
    })
  })

  it('Clear triggers confirm and calls clearConfig when confirmed', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    mockConfirm.mockResolvedValueOnce(true)
    const user = userEvent.setup()
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('settings.llm.clear'))

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalledTimes(1)
      expect(mockClearConfig).toHaveBeenCalledTimes(1)
    })
    expect(toast.success).toHaveBeenCalled()
  })

  it('Clear does nothing when confirm is canceled', async () => {
    mockGetConfig.mockResolvedValue({ ...sampleConfig, enabled: true })
    mockConfirm.mockResolvedValueOnce(false)
    const user = userEvent.setup()
    renderWithQuery(<LlmSettings />)
    await screen.findByText('settings.llm.hint')
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('settings.llm.clear'))

    expect(mockConfirm).toHaveBeenCalledTimes(1)
    expect(mockClearConfig).not.toHaveBeenCalled()
  })
})