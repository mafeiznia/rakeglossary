import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  ExternalLink,
  Eye,
  EyeOff,
  Loader2,
  RefreshCw,
  Save,
  Sparkles,
  Trash2,
  X,
  XCircle,
  Zap,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tooltip } from '@/components/ui/tooltip'
import {
  llmApi,
  type LlmConfigRead,
  type LlmModelsRead,
  type LlmTestResult,
} from '@/api/llm'
import { useConfirm } from '@/features/confirm/confirmStore'

export function LlmSettings() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const confirm = useConfirm()

  const providersQuery = useQuery({
    queryKey: ['llm', 'providers'],
    queryFn: llmApi.getProviders,
    staleTime: Infinity,
  })

  const configQuery = useQuery({
    queryKey: ['llm', 'config'],
    queryFn: llmApi.getConfig,
  })

  const [enabled, setEnabled] = useState(false)
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [testResult, setTestResult] = useState<LlmTestResult | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [initialized, setInitialized] = useState(false)

  // --- Models list ---
  const modelsQuery = useQuery({
    queryKey: ['llm', 'models', provider],
    queryFn: () => llmApi.getModels(provider),
    enabled: enabled && !!provider,
    staleTime: 60_000,
  })

  const refreshModelsMutation = useMutation({
    mutationFn: () => llmApi.refreshModels(provider),
    onSuccess: (data) => {
      qc.setQueryData(['llm', 'models', provider], data)
      toast.success(
        t('settings.llm.modelList.refreshSuccess', {
          count: data.models.length,
        })
      )
    },
    onError: (err) => {
      toast.error(
        t('settings.llm.modelList.refreshFailed', {
          message: (err as Error).message,
        })
      )
    },
  })

  const removeModelMutation = useMutation({
    mutationFn: (m: string) => llmApi.deleteUserModel(provider, m),
    onSuccess: (_, removedModel) => {
      qc.invalidateQueries({ queryKey: ['llm', 'models', provider] })
      toast.success(t('settings.llm.modelList.removed'))
      // If we removed the currently selected model, clear the input
      if (removedModel === model) {
        setModel('')
      }
    },
  })  

  useEffect(() => {
    const cfg = configQuery.data
    if (!cfg || initialized) return
    setEnabled(cfg.enabled)
    setProvider(cfg.provider)
    setModel(cfg.model)
    setApiKey('')
    setInitialized(true)
  }, [configQuery.data, initialized])

  const currentProvider = providersQuery.data?.find((p) => p.key === provider)


  // Helper: is a model in the user's history for the current provider?
  const isInUserHistory = (m: string): boolean =>
    modelsQuery.data?.user_models?.includes(m) ?? false

  // Helper: is a model coming from the fetched cache (but not user history)?
  const isInCache = (m: string): boolean =>
    (modelsQuery.data?.cached_models?.includes(m) ?? false) &&
    !isInUserHistory(m)
    
  const handleProviderChange = (key: string) => {
    setProvider(key)
    const p = providersQuery.data?.find((x) => x.key === key)
    if (p) setModel(p.default_model)
    setTestResult(null)
  }

  const buildPayload = () => ({
    enabled,
    provider,
    model,
    ...(apiKey ? { api_key: apiKey } : {}),
  })

  const saveMutation = useMutation({
    mutationFn: () => llmApi.updateConfig(buildPayload()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['llm', 'config'] })
      setApiKey('')
      setTestResult(null)
      setSaveMessage(t('settings.llm.savedOk'))
      toast.success(t('toast.saved'))
      setTimeout(() => setSaveMessage(null), 2000)
    },
  })

  const testMutation = useMutation({
    mutationFn: async () => {
      await llmApi.updateConfig({ ...buildPayload(), enabled: true })
      return llmApi.testConfig()
    },
    onSuccess: (data) => {
      setTestResult(data)
      setEnabled(true)
      qc.invalidateQueries({ queryKey: ['llm', 'config'] })
    },
    onError: (err) =>
      setTestResult({
        success: false,
        message: (err as Error).message,
        latency_ms: null,
      }),
  })

  const clearMutation = useMutation({
    mutationFn: llmApi.clearConfig,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['llm', 'config'] })
      setApiKey('')
      setTestResult(null)
      setInitialized(false)
      toast.success(t('toast.saved'))
    },
  })

  const handleSave = () => {
    setSaveMessage(null)
    saveMutation.mutate()
  }

  const handleTest = () => {
    setTestResult(null)
    setSaveMessage(null)
    testMutation.mutate()
  }

  const handleClear = async () => {
    const ok = await confirm({
      title: t('confirm.clearLlm.title'),
      description: t('confirm.clearLlm.description'),
      confirmLabel: t('common.delete'),
      variant: 'destructive',
    })
    if (!ok) return
    clearMutation.mutate()
  }

  if (configQuery.isLoading || providersQuery.isLoading) {
    return (
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">{t('settings.llm.title')}</h3>
        <div
          className="flex items-center gap-2 text-sm"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          <Loader2 className="h-4 w-4 animate-spin" />
          {t('common.loading')}
        </div>
      </section>
    )
  }

  const cfg: LlmConfigRead | undefined = configQuery.data

  return (
    <section className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">{t('settings.llm.title')}</h3>
          <p
            className="text-xs mt-1"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {t('settings.llm.hint')}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Tooltip content="اگر خاموش باشد، حالت‌های AI و Hybrid در دسترس نیستند.">
            <span className="text-sm cursor-help">
              {t('settings.llm.enabled')}
            </span>
          </Tooltip>
          <Switch checked={enabled} onCheckedChange={setEnabled} />
        </div>
      </div>

      {enabled && (
        <div
          className="rounded-lg border p-4 space-y-4"
          style={{
            backgroundColor: 'rgb(var(--color-surface))',
            borderColor: 'rgb(var(--color-border))',
          }}
        >
          {/* Provider */}
          <div className="space-y-2">
            <Label htmlFor="llm-provider">
              <Tooltip content="سرویس‌دهنده‌ی هوش مصنوعی. هر provider قیمت و کیفیت متفاوتی دارد.">
                <span className="cursor-help">
                  {t('settings.llm.provider')} ⓘ
                </span>
              </Tooltip>
            </Label>
            <select
              id="llm-provider"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full max-w-sm rounded-md border px-3 py-2 text-sm"
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
                className="inline-flex items-center gap-1 text-xs hover:underline"
                style={{ color: 'rgb(var(--color-primary))' }}
              >
                {t('settings.llm.getKey')}
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>

          {/* API key */}
          <div className="space-y-2">
            <Label htmlFor="llm-key">
              <Tooltip content="کلید API که از سایت provider گرفته‌ای. به‌صورت محلی در دیتابیس ذخیره می‌شود.">
                <span className="cursor-help">
                  {t('settings.llm.apiKey')} ⓘ
                </span>
              </Tooltip>
            </Label>
            <div className="flex gap-2 max-w-md">
              <div className="relative flex-1">
                <Input
                  id="llm-key"
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={
                    cfg?.has_api_key
                      ? `${t('settings.llm.keyStored')} ${cfg.api_key_masked}`
                      : t('settings.llm.keyPlaceholder')
                  }
                  autoComplete="off"
                />
                <Tooltip content={showKey ? 'پنهان کردن' : 'نمایش دادن'}>
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
                </Tooltip>
              </div>
            </div>
            <p
              className="text-xs"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              {t('settings.llm.keyHint')}
            </p>
          </div>

          {/* Model */}
          <div className="space-y-2">
            <Label htmlFor="llm-model">
              <Tooltip content="نام مدل هوش مصنوعی. مدل‌های مختلف قیمت و سرعت متفاوتی دارند. می‌توانی از لیست پیشنهادی انتخاب کنی یا دستی تایپ کنی.">
                <span className="cursor-help">
                  {t('settings.llm.model')} ⓘ
                </span>
              </Tooltip>
            </Label>

            <div className="flex gap-2 max-w-md">
              <Input
                id="llm-model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={currentProvider?.default_model}
                list="llm-model-suggestions"
                className="flex-1"
              />
              <Tooltip content={t('settings.llm.modelList.refresh')}>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => refreshModelsMutation.mutate()}
                  disabled={
                    refreshModelsMutation.isPending ||
                    !cfg?.has_api_key
                  }
                >
                  {refreshModelsMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                </Button>
              </Tooltip>
            </div>

            {currentProvider && (
              <datalist id="llm-model-suggestions">
                {modelsQuery.data?.models.map((m) => (
                  <option key={m} value={m} />
                ))}
              </datalist>
            )}

            <p
              className="text-xs"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              {t('settings.llm.modelList.hint')}
            </p>

            {/* Model list */}
            {modelsQuery.data && modelsQuery.data.models.length > 0 && (
              <div
                className="rounded-md border max-w-md max-h-56 overflow-y-auto"
                style={{ borderColor: 'rgb(var(--color-border))' }}
              >
                <ul className="divide-y" style={{ borderColor: 'rgb(var(--color-border))' }}>
                  {modelsQuery.data.models.map((m) => {
                    const isCurrent = m === model
                    const isUser = isInUserHistory(m)
                    const isCached = !isUser && isInCache(m)
                    return (
                      <li
                        key={m}
                        className="flex items-center justify-between gap-2 px-3 py-1.5 text-sm cursor-pointer hover:bg-opacity-50"
                        style={{
                          backgroundColor: isCurrent
                            ? 'rgb(var(--color-primary) / 0.1)'
                            : undefined,
                        }}
                        onClick={() => setModel(m)}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate font-mono text-xs">
                            {m}
                          </span>
                          {isUser && (
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded shrink-0"
                              style={{
                                backgroundColor:
                                  'rgb(var(--color-primary) / 0.15)',
                                color: 'rgb(var(--color-primary))',
                              }}
                            >
                              {t('settings.llm.modelList.userBadge')}
                            </span>
                          )}
                          {isCached && (
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded shrink-0"
                              style={{
                                backgroundColor:
                                  'rgb(var(--color-info) / 0.15)',
                                color: 'rgb(var(--color-info))',
                              }}
                            >
                              {t('settings.llm.modelList.cachedBadge')}
                            </span>
                          )}
                        </div>
                        {isUser && (
                          <Tooltip
                            content={t('settings.llm.modelList.removeFromHistory')}
                          >
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                removeModelMutation.mutate(m)
                              }}
                              className="opacity-50 hover:opacity-100 shrink-0"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          </Tooltip>
                        )}
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2">
            <Tooltip content="ذخیره تنظیمات برای استفاده‌های بعدی">
              <Button onClick={handleSave} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {t('common.save')}
              </Button>
            </Tooltip>
            <Tooltip content="ارسال یک درخواست آزمایشی به provider تا مطمئن شوی تنظیمات درست است. قبل از تست، تنظیمات خودکار ذخیره می‌شوند.">
              <Button
                variant="outline"
                onClick={handleTest}
                disabled={
                  testMutation.isPending || (!apiKey && !cfg?.has_api_key)
                }
              >
                {testMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                {t('settings.llm.test')}
              </Button>
            </Tooltip>
            <Tooltip content="حذف کامل کلید API و همه تنظیمات LLM از دیتابیس">
              <Button
                variant="ghost"
                onClick={handleClear}
                disabled={clearMutation.isPending}
              >
                <Trash2
                  className="h-4 w-4"
                  style={{ color: 'rgb(var(--color-error))' }}
                />
                {t('settings.llm.clear')}
              </Button>
            </Tooltip>
          </div>

          {saveMessage && !testResult && (
            <div
              className="rounded-md border p-3 text-sm flex items-start gap-2"
              style={{
                borderColor: 'rgb(var(--color-success))',
                color: 'rgb(var(--color-success))',
              }}
            >
              <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
              <div>{saveMessage}</div>
            </div>
          )}

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
                    {t('settings.llm.latency', { ms: testResult.latency_ms })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}