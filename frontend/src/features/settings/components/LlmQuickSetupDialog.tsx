import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Save,
  XCircle,
  Zap,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { llmApi, type LlmTestResult } from '@/api/llm'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved?: () => void
}

export function LlmQuickSetupDialog({ open, onOpenChange, onSaved }: Props) {
  const { t } = useTranslation()
  const qc = useQueryClient()

  const providersQuery = useQuery({
    queryKey: ['llm', 'providers'],
    queryFn: llmApi.getProviders,
    staleTime: Infinity,
    enabled: open,
  })

  const configQuery = useQuery({
    queryKey: ['llm', 'config'],
    queryFn: llmApi.getConfig,
    enabled: open,
  })

  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [testResult, setTestResult] = useState<LlmTestResult | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  // Only initialize the form ONCE when the dialog opens. This prevents
  // useEffect from re-running (and wiping testResult) after every refetch.
  const initializedRef = useRef(false)

  useEffect(() => {
    if (!open) {
      // Reset the flag so the next open re-initializes
      initializedRef.current = false
      return
    }
    if (!configQuery.data || initializedRef.current) return

    const cfg = configQuery.data
    setProvider(cfg.provider)
    setModel(cfg.model)
    setBaseUrl(cfg.base_url ?? '')
    setApiKey('')
    setTestResult(null)
    setSaveMessage(null)
    initializedRef.current = true
  }, [open, configQuery.data])

  const currentProvider = providersQuery.data?.find((p) => p.key === provider)
  const isCustom = provider === 'custom'
  const hasStoredKey = Boolean(configQuery.data?.has_api_key)

  const handleProviderChange = (key: string) => {
    setProvider(key)
    const p = providersQuery.data?.find((x) => x.key === key)
    if (p) setModel(p.default_model)
    if (key !== 'custom') setBaseUrl('')
    setTestResult(null)
    setSaveMessage(null)
    // If user changes provider, clear the typed key. If they had a stored
    // key for a different provider, the backend will clear it on save.
    setApiKey('')
  }

  const buildPayload = (enable: boolean) => ({
    enabled: enable,
    provider,
    model,
    ...(apiKey ? { api_key: apiKey } : {}),
    ...(isCustom ? { base_url: baseUrl || null } : {}),
  })

  /**
   * Save — persists config, shows success message, closes dialog after
   * a short delay.
   */
  const saveMutation = useMutation({
    mutationFn: () => llmApi.updateConfig(buildPayload(true)),
    onSuccess: async () => {
      qc.invalidateQueries({ queryKey: ['llm', 'config'] })
      setSaveMessage(t('settings.llm.savedOk'))
      setTimeout(() => {
        onSaved?.()
        onOpenChange(false)
      }, 700)
    },
    onError: (err) => {
      setSaveMessage(`${t('common.error')}: ${(err as Error).message}`)
    },
  })

  /**
   * Test — persists current values (so the server has them), then calls
   * the test endpoint. The result is shown in the dialog.
   *
   * IMPORTANT: we do NOT invalidate `llm/config` here, because that would
   * trigger a refetch and (via the init effect) clear our test result.
   * We only invalidate after a SUCCESSFUL save or test, but only after
   * a short delay so the user sees the result first.
   */
  const testMutation = useMutation({
    mutationFn: async () => {
      // Persist current form values so the server tests what the user sees
      await llmApi.updateConfig(buildPayload(true))
      // Then run the test
      return llmApi.testConfig()
    },
    onSuccess: (data) => {
      setTestResult(data)
      // Refresh the stored-key mask in the background, but don't reset
      // our test result.
      qc.invalidateQueries({ queryKey: ['llm', 'config'] })
    },
    onError: (err) =>
      setTestResult({
        success: false,
        message: (err as Error).message,
        latency_ms: null,
      }),
  })

  const canSave =
    !saveMutation.isPending &&
    (apiKey || hasStoredKey) &&
    model.trim().length > 0 &&
    (!isCustom || baseUrl.trim().length > 0)

  const canTest =
    !testMutation.isPending &&
    (apiKey || hasStoredKey) &&
    model.trim().length > 0 &&
    (!isCustom || baseUrl.trim().length > 0)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('settings.llm.quickSetupTitle')}</DialogTitle>
          <DialogDescription>
            {t('settings.llm.quickSetupHint')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Provider */}
          <div className="space-y-2">
            <Label htmlFor="dialog-provider">
              {t('settings.llm.provider')}
            </Label>
            <select
              id="dialog-provider"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              style={{
                backgroundColor: 'rgb(var(--color-surface))',
                borderColor: 'rgb(var(--color-border))',
                color: 'rgb(var(--color-text))',
              }}
            >
              {providersQuery.data?.map((p) => (
                <option key={p.key} value={p.key}>
                  {p.name}
                </option>
              ))}
            </select>
            {currentProvider?.docs_url && (
              <a
                href={currentProvider.docs_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs hover:underline"
                style={{ color: 'rgb(var(--color-primary))' }}
              >
                {t('settings.llm.getKey')}
              </a>
            )}
          </div>

          {/* API key */}
          <div className="space-y-2">
            <Label htmlFor="dialog-api-key">{t('settings.llm.apiKey')}</Label>
            <div className="relative">
              <Input
                id="dialog-api-key"
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={
                  hasStoredKey && configQuery.data?.provider === provider
                    ? `${t('settings.llm.keyStored')} ${configQuery.data?.api_key_masked}`
                    : t('settings.llm.keyPlaceholder')
                }
                autoComplete="off"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute end-2 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100"
              >
                {showKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {hasStoredKey && configQuery.data?.provider === provider && !apiKey && (
              <p
                className="text-xs"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {t('settings.llm.keepExistingKey')}
              </p>
            )}
            {hasStoredKey && configQuery.data?.provider !== provider && (
              <p
                className="text-xs"
                style={{ color: 'rgb(var(--color-warning))' }}
              >
                {t('settings.llm.newKeyRequired')}
              </p>
            )}
          </div>

          {/* Custom base URL */}
          {isCustom && (
            <div className="space-y-2">
              <Label htmlFor="dialog-base-url">
                {t('settings.llm.baseUrl')}
              </Label>
              <Input
                id="dialog-base-url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.example.com/v1"
              />
            </div>
          )}

          {/* Model */}
          <div className="space-y-2">
            <Label htmlFor="dialog-model">{t('settings.llm.model')}</Label>
            <Input
              id="dialog-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder={currentProvider?.default_model}
              list="dialog-llm-model-suggestions"
            />
            {currentProvider &&
              currentProvider.suggested_models.length > 0 && (
                <datalist id="dialog-llm-model-suggestions">
                  {currentProvider.suggested_models.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              )}
          </div>

          {/* Test result */}
          {testResult && (
            <div
              className="rounded-md border p-3 text-sm flex items-start gap-2"
              style={{
                borderColor: testResult.success
                  ? 'rgb(var(--color-success))'
                  : 'rgb(var(--color-error))',
                color: testResult.success
                  ? 'rgb(var(--color-success))'
                  : 'rgb(var(--color-error))',
              }}
            >
              {testResult.success ? (
                <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
              )}
              <div className="min-w-0">
                <div className="break-words">{testResult.message}</div>
                {testResult.latency_ms !== null && (
                  <div
                    className="text-xs mt-1"
                    style={{ color: 'rgb(var(--color-text-muted))' }}
                  >
                    {t('settings.llm.latency', {
                      ms: testResult.latency_ms,
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Save message */}
          {saveMessage && !testResult && (
            <div
              className="rounded-md border p-2 text-xs"
              style={{
                borderColor: 'rgb(var(--color-success))',
                color: 'rgb(var(--color-success))',
              }}
            >
              {saveMessage}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={saveMutation.isPending || testMutation.isPending}
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="outline"
            onClick={() => testMutation.mutate()}
            disabled={!canTest}
          >
            {testMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            {t('settings.llm.test')}
          </Button>
          <Button onClick={() => saveMutation.mutate()} disabled={!canSave}>
            {saveMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {t('settings.llm.saveAndClose')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}