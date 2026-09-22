import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle2,
  ChevronDown,
  Settings2,
  Sparkles,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tooltip } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { llmApi } from '@/api/llm'
import { LlmQuickSetupDialog } from '@/features/settings/components/LlmQuickSetupDialog'
import type { ProcessingMode, ProcessRequest } from '@/types'

interface Props {
  options: ProcessRequest
  onChange: (opts: ProcessRequest) => void
  /** If true, the panel starts expanded. */
  defaultOpen?: boolean
  /** If set, the panel will expand when this key changes. */
  expandKey?: number
}

interface RowProps {
  label: string
  checked: boolean
  onCheckedChange: (v: boolean) => void
  tooltip?: string
}

function SwitchRow({ label, checked, onCheckedChange, tooltip }: RowProps) {
  const labelEl = (
    <span className="text-sm cursor-help">{label}</span>
  )
  return (
    <div className="flex items-center justify-between py-2">
      {tooltip ? (
        <Tooltip content={tooltip}>{labelEl}</Tooltip>
      ) : (
        labelEl
      )}
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  )
}

interface ModeCardProps {
  value: ProcessingMode
  current: ProcessingMode
  onSelect: (v: ProcessingMode) => void
  title: string
  hint: string
  details: string[]
  icon: typeof Wifi
  tooltip?: string
}

function ModeCard({
  value,
  current,
  onSelect,
  title,
  hint,
  details,
  icon: Icon,
  tooltip,
}: ModeCardProps) {
  const isSelected = value === current
  const card = (
    <button
      type="button"
      onClick={() => onSelect(value)}
      className="rounded-lg border-2 p-3 text-start transition-all w-full"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: isSelected
          ? 'rgb(var(--color-primary))'
          : 'rgb(var(--color-border))',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon
          className="h-4 w-4"
          style={{
            color: isSelected
              ? 'rgb(var(--color-primary))'
              : 'rgb(var(--color-text-muted))',
          }}
        />
        <span className="text-sm font-semibold">{title}</span>
      </div>
      <div
        className="text-xs mb-2"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        {hint}
      </div>
      <ul className="text-xs space-y-0.5">
        {details.map((d, i) => (
          <li key={i} style={{ color: 'rgb(var(--color-text-muted))' }}>
            · {d}
          </li>
        ))}
      </ul>
    </button>
  )
  return tooltip ? <Tooltip content={tooltip}>{card}</Tooltip> : card
}

export function OptionsPanel({
  options,
  onChange,
  defaultOpen,
  expandKey,
}: Props) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(!!defaultOpen)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    if (expandKey !== undefined) {
      setOpen(true)
    }
  }, [expandKey])

  const llmConfigQuery = useQuery({
    queryKey: ['llm', 'config'],
    queryFn: llmApi.getConfig,
    staleTime: 15_000,
  })
  const llmReady = Boolean(
    llmConfigQuery.data?.enabled && llmConfigQuery.data?.has_api_key
  )

  const set = <K extends keyof ProcessRequest>(
    key: K,
    value: ProcessRequest[K]
  ) => onChange({ ...options, [key]: value })

  const needsLlm =
    options.processing_mode === 'ai' || options.processing_mode === 'hybrid'

  return (
    <>
      <div
        className="rounded-lg border"
        style={{
          backgroundColor: 'rgb(var(--color-surface))',
          borderColor: 'rgb(var(--color-border))',
        }}
      >
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex w-full items-center justify-between p-4 text-start"
        >
          <span className="text-sm font-semibold">
            {t('home.optionsToggle')}
          </span>
          <ChevronDown
            className={cn(
              'h-4 w-4 transition-transform',
              open && 'rotate-180'
            )}
          />
        </button>

        {open && (
          <div
            className="border-t p-4 space-y-6 rg-anim-fade-up"
            style={{ borderColor: 'rgb(var(--color-border))' }}
          >
            {/* Processing mode */}
            <div className="space-y-2">
              <Label>{t('home.processingMode')}</Label>
              <p
                className="text-xs"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {t('home.processingModeHint')}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
                <ModeCard
                  value="offline"
                  current={options.processing_mode}
                  onSelect={(v) => set('processing_mode', v)}
                  title={t('home.modeOffline')}
                  hint={t('home.modeOfflineHint')}
                  details={[
                    t('home.modeOfflineDetails1'),
                    t('home.modeOfflineDetails2'),
                    t('home.modeOfflineDetails3'),
                  ]}
                  icon={WifiOff}
                  tooltip="کاملاً آفلاین. تعریف‌ها از Wikipedia و WordNet گرفته می‌شوند و ترجمه با Argos انجام می‌شود. سریع، رایگان، ولی کیفیت ترجمه محدودتر."
                />
                <ModeCard
                  value="ai"
                  current={options.processing_mode}
                  onSelect={(v) => set('processing_mode', v)}
                  title={t('home.modeAi')}
                  hint={t('home.modeAiHint')}
                  details={[
                    t('home.modeAiDetails1'),
                    t('home.modeAiDetails2'),
                    t('home.modeAiDetails3'),
                  ]}
                  icon={Sparkles}
                  tooltip="هوش مصنوعی هم واژه‌ها را انتخاب می‌کند، هم ترجمه می‌کند و هم تعریف می‌نویسد. بهترین کیفیت ولی نیاز به API key."
                />
                <ModeCard
                  value="hybrid"
                  current={options.processing_mode}
                  onSelect={(v) => set('processing_mode', v)}
                  title={t('home.modeHybrid')}
                  hint={t('home.modeHybridHint')}
                  details={[
                    t('home.modeHybridDetails1'),
                    t('home.modeHybridDetails2'),
                    t('home.modeHybridDetails3'),
                  ]}
                  icon={Wifi}
                  tooltip="ترکیبی: واژه‌ها و تعریف‌ها با روش‌های رایگان (NLP کلاسیک + Wikipedia)، ولی ترجمه با LLM انجام می‌شود. تعادل بین کیفیت و هزینه."
                />
              </div>

              {options.processing_mode === 'offline' && (
                <p
                  className="text-xs mt-2 italic"
                  style={{ color: 'rgb(var(--color-text-muted))' }}
                >
                  {t('home.modeOfflineWarning')}
                </p>
              )}

              {needsLlm && (
                <div
                  className="flex flex-wrap items-center justify-between gap-2 mt-3 p-3 rounded-md border"
                  style={{
                    borderColor: llmReady
                      ? 'rgb(var(--color-success))'
                      : 'rgb(var(--color-warning))',
                    backgroundColor: 'rgb(var(--color-surface-alt))',
                  }}
                >
                  {llmReady ? (
                    <span
                      className="text-xs flex items-center gap-1.5"
                      style={{ color: 'rgb(var(--color-success))' }}
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {t('home.llmReady')}
                      {llmConfigQuery.data?.provider && (
                        <>
                          {' '}
                          ({llmConfigQuery.data.provider} /{' '}
                          {llmConfigQuery.data.model})
                        </>
                      )}
                    </span>
                  ) : (
                    <span
                      className="text-sm"
                      style={{ color: 'rgb(var(--color-warning))' }}
                    >
                      {t('home.modeRequiresLlm')}
                    </span>
                  )}
                  <Tooltip content="تنظیم API key، انتخاب provider و مدل">
                    <Button
                      size="sm"
                      variant={llmReady ? 'outline' : 'default'}
                      onClick={() => setDialogOpen(true)}
                    >
                      <Settings2 className="h-3.5 w-3.5" />
                      {llmReady ? t('home.editLlm') : t('home.setupLlmNow')}
                    </Button>
                  </Tooltip>
                </div>
              )}
            </div>

            {/* Term density */}
            <div className="space-y-2">
              <Label htmlFor="terms-per-1k">
                <Tooltip content="هرچه این عدد بالاتر باشد، واژه‌های بیشتری استخراج می‌شود. مثال: برای کتاب ۲۰٬۰۰۰ کلمه‌ای، مقدار ۱۵ یعنی حدود ۳۰۰ واژه.">
                  <span className="cursor-help">{t('home.termsPer1k')} ⓘ</span>
                </Tooltip>
              </Label>
              <Input
                id="terms-per-1k"
                type="number"
                min={1}
                max={100}
                step={0.5}
                value={options.terms_per_1k_words}
                onChange={(e) =>
                  set(
                    'terms_per_1k_words',
                    Math.max(1, Math.min(100, Number(e.target.value) || 15))
                  )
                }
                className="max-w-[140px]"
              />
              <p
                className="text-xs"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {t('home.termsPer1kHint')}
              </p>
            </div>

            {/* Max cap */}
            <div className="space-y-2">
              <Label htmlFor="max-terms">
                <Tooltip content="سقف نهایی تعداد واژه‌ها. اگر چگالی واژگان عدد بزرگ‌تری بدهد، این سقف اعمال می‌شود.">
                  <span className="cursor-help">{t('home.maxTerms')} ⓘ</span>
                </Tooltip>
              </Label>
              <Input
                id="max-terms"
                type="number"
                min={1}
                max={2000}
                value={options.num_terms}
                onChange={(e) =>
                  set(
                    'num_terms',
                    Math.max(1, Math.min(2000, Number(e.target.value) || 500))
                  )
                }
                className="max-w-[140px]"
              />
              <p
                className="text-xs"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {t('home.maxTermsHint')}
              </p>
            </div>

            {/* Translation */}
            <div>
              <h4 className="text-sm font-semibold mb-2">
                {t('home.translationSection')}
              </h4>
              <SwitchRow
                label={t('home.translateTerms')}
                checked={options.translate_terms}
                onCheckedChange={(v) => set('translate_terms', v)}
                tooltip="اگر خاموش باشد، فقط واژه‌های انگلیسی استخراج می‌شوند و ستون فارسی خالی می‌ماند."
              />
              <SwitchRow
                label={t('home.translateDefinitions')}
                checked={options.translate_definitions}
                onCheckedChange={(v) => set('translate_definitions', v)}
                tooltip="اگر خاموش باشد، تعریف‌های انگلیسی استخراج می‌شوند ولی ترجمه نمی‌شوند. برای صرفه‌جویی در هزینه مفید است."
              />
              <p
                className="text-xs mt-2"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                {options.processing_mode === 'offline'
                  ? t('home.translationViaOffline')
                  : t('home.translationViaLlm')}
              </p>
            </div>

            {/* NLP */}
            <div>
              <h4 className="text-sm font-semibold mb-2">
                <Tooltip content="روش‌های کلاسیک استخراج واژه. فقط در حالت‌های Offline و Hybrid استفاده می‌شوند. در حالت AI، انتخاب واژه‌ها با LLM انجام می‌شود.">
                  <span className="cursor-help">
                    {t('home.nlpSection')} ⓘ
                  </span>
                </Tooltip>
              </h4>
              <SwitchRow
                label={t('home.useSpacy')}
                checked={options.use_spacy}
                onCheckedChange={(v) => set('use_spacy', v)}
                tooltip="استخراج عبارت‌های اسمی (Noun Chunks) با spaCy. ستون فقرات استخراج واژه است."
              />
              <SwitchRow
                label={t('home.useRake')}
                checked={options.use_rake}
                onCheckedChange={(v) => set('use_rake', v)}
                tooltip="الگوریتم RAKE: واژه‌های مهم را بر اساس co-occurrence شناسایی می‌کند. مکمل خوبی برای spaCy."
              />
              <SwitchRow
                label={t('home.useYake')}
                checked={options.use_yake}
                onCheckedChange={(v) => set('use_yake', v)}
                tooltip="الگوریتم YAKE: بدون نیاز به آموزش، واژه‌های کلیدی را بر اساس آمار متن پیدا می‌کند."
              />
              <SwitchRow
                label={t('home.useNer')}
                checked={options.use_ner}
                onCheckedChange={(v) => set('use_ner', v)}
                tooltip="تشخیص اسامی خاص (اشخاص، مکان‌ها، سازمان‌ها) با spaCy NER. برای کتاب‌های داستانی و تاریخی مفید است."
              />
            </div>
          </div>
        )}
      </div>

      {/* Modal for quick LLM setup */}
      <LlmQuickSetupDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSaved={() => {
          // The dialog invalidates the query itself; nothing else to do.
        }}
      />
    </>
  )
}