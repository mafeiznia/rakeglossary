/**
 * Tests for LlmQuickSetupDialog.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// --- llmApi ---
const mockGetProviders = vi.fn()
const mockGetConfig = vi.fn()
const mockUpdateConfig = vi.fn()
const mockTestConfig = vi.fn()

vi.mock('@/api/llm', () => ({
  llmApi: {
    getProviders: () => mockGetProviders(),
    getConfig: () => mockGetConfig(),
    updateConfig: (payload: unknown) => mockUpdateConfig(payload),
    testConfig: () => mockTestConfig(),
    clearConfig: vi.fn(),
  },
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
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div data-testid="dialog-root">{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => (
    <div data-testid="dialog-content">{children}</div>
  ),
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

import { LlmQuickSetupDialog } from '@/features/settings/components/LlmQuickSetupDialog'

const providers = [
  {
    key: 'openai',
    name: 'OpenAI',
    default_model: 'gpt-4o-mini',
    suggested_models: ['gpt-4o-mini'],
    docs_url: 'https://openai.com/keys',
  },
  {
    key: 'custom',
    name: 'Custom',
    default_model: '',
    suggested_models: [],
    docs_url: null,
  },
]

const configDisabled = {
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

describe('LlmQuickSetupDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetProviders.mockResolvedValue(providers)
    mockGetConfig.mockResolvedValue(configDisabled)
    mockUpdateConfig.mockResolvedValue({})
    mockTestConfig.mockResolvedValue({
      success: true,
      message: 'pong',
      latency_ms: 10,
    })
  })

  it('renders nothing when closed', () => {
    renderWithQuery(
      <LlmQuickSetupDialog open={false} onOpenChange={vi.fn()} />
    )
    expect(screen.queryByTestId('dialog-root')).not.toBeInTheDocument()
  })

  it('renders dialog content when open', async () => {
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    expect(screen.getByTestId('dialog-root')).toBeInTheDocument()
    expect(
      screen.getByText('settings.llm.quickSetupTitle')
    ).toBeInTheDocument()
    await waitFor(() => screen.getByText('OpenAI'))
  })

  it('renders all providers in select', async () => {
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument()
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })
  })

  it('shows base_url field only when custom provider is selected', async () => {
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    const select = screen.getByLabelText(
      'settings.llm.provider'
    ) as HTMLSelectElement
    await user.selectOptions(select, 'custom')

    expect(
      screen.getByLabelText('settings.llm.baseUrl')
    ).toBeInTheDocument()
  })

  it('Save button is disabled when no key and no stored key', async () => {
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    const saveBtn = screen
      .getByText('settings.llm.saveAndClose')
      .closest('button')
    expect(saveBtn).toBeDisabled()
  })

  it('Save button is enabled after typing a key', async () => {
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    await user.type(
      screen.getByLabelText('settings.llm.apiKey'),
      'sk-test-key'
    )
    const saveBtn = screen
      .getByText('settings.llm.saveAndClose')
      .closest('button')
    expect(saveBtn).not.toBeDisabled()
  })

  it('Cancel calls onOpenChange(false)', async () => {
    const onOpenChange = vi.fn()
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={onOpenChange} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    await user.click(screen.getByText('common.cancel'))
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('Save calls updateConfig with provided key', async () => {
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    await user.type(
      screen.getByLabelText('settings.llm.apiKey'),
      'sk-new-key'
    )
    await user.click(screen.getByText('settings.llm.saveAndClose'))

    await waitFor(() => {
      expect(mockUpdateConfig).toHaveBeenCalledTimes(1)
    })
    const payload = mockUpdateConfig.mock.calls[0][0]
    expect(payload.api_key).toBe('sk-new-key')
    expect(payload.provider).toBe('openai')
    expect(payload.enabled).toBe(true)
  })

  it('Test calls updateConfig then testConfig and shows result', async () => {
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    await user.type(
      screen.getByLabelText('settings.llm.apiKey'),
      'sk-new-key'
    )
    await user.click(screen.getByText('settings.llm.test'))

    await waitFor(() => {
      expect(mockUpdateConfig).toHaveBeenCalledTimes(1)
      expect(mockTestConfig).toHaveBeenCalledTimes(1)
      expect(screen.getByText('pong')).toBeInTheDocument()
    })
  })

  it('Test failure shows error message', async () => {
    mockTestConfig.mockResolvedValue({
      success: false,
      message: 'invalid key',
      latency_ms: null,
    })
    const user = userEvent.setup()
    renderWithQuery(
      <LlmQuickSetupDialog open={true} onOpenChange={vi.fn()} />
    )
    await waitFor(() => screen.getByText('OpenAI'))

    await user.type(
      screen.getByLabelText('settings.llm.apiKey'),
      'sk-bad'
    )
    await user.click(screen.getByText('settings.llm.test'))

    await waitFor(() => {
      expect(screen.getByText('invalid key')).toBeInTheDocument()
    })
  })
})