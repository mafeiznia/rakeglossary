import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  AlertCircle,
  ChevronDown,
  FileJson,
  FileUp,
  FormInput,
  Loader2,
  Save,
  Trash2,
  Upload,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tooltip } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

type MetadataSource = 'manual' | 'json' | null

export interface BookMetadataValue extends Record<string, unknown> {
  metadata_source?: MetadataSource
  metadata_filename?: string
}

interface Props {
  value: BookMetadataValue | null
  onChange: (next: BookMetadataValue | null) => void
  isSaving?: boolean
  defaultCollapsed?: boolean
  initialTab?: 'manual' | 'json'
}

// --- Language helpers --------------------------------------------------------

function containsPersian(text: string): boolean {
  for (const c of text) {
    const code = c.charCodeAt(0)
    if (
      (code >= 0x0600 && code <= 0x06ff) ||
      (code >= 0xfb50 && code <= 0xfdff)
    ) {
      return true
    }
  }
  return false
}

function containsLatin(text: string): boolean {
  return /[A-Za-z]/.test(text)
}

// --- Metadata helpers --------------------------------------------------------

function detectSource(value: BookMetadataValue | null): MetadataSource {
  if (!value) return null
  const explicit = value.metadata_source
  if (explicit === 'manual' || explicit === 'json') return explicit
  return 'manual'
}

function manualFieldsFromValue(v: BookMetadataValue | null) {
  const book = (v?.book_metadata as Record<string, unknown>) || {}
  const cc = (v?.content_classification as Record<string, unknown>) || {}
  const setting = (cc?.setting as Record<string, unknown>) || {}
  const aa = (v?.audience_analysis as Record<string, unknown>) || {}
  const sa = (v?.stylistic_analysis as Record<string, unknown>) || {}
  const tg = (v?.translation_guidelines as Record<string, unknown>) || {}

  const toArr = (x: unknown): string => {
    if (Array.isArray(x)) return x.join(', ')
    if (typeof x === 'string') return x
    return ''
  }

  return {
    title: String(book.title || ''),
    originalTitle: String(book.original_title || ''),
    author: String(book.author || ''),
    primaryGenre: String(cc.primary_genre || ''),
    subGenres: toArr(cc.sub_genres),
    mainThemes: toArr(cc.main_themes),
    timePeriod: String(setting.time_period || ''),
    location: String(setting.location || ''),
    targetAudience: String(aa.target_audience || ''),
    readingLevel: String(aa.reading_level || ''),
    vocabularyComplexity: String(sa.vocabulary_complexity || ''),
    culturalContext: String(tg.cultural_context || ''),
    keyTerminology: Array.isArray(tg.key_terminology)
      ? (tg.key_terminology as Array<Record<string, unknown>>)
          .map((t) =>
            t.term
              ? t.suggested_translation
                ? `${t.term}=${t.suggested_translation}`
                : `${t.term}`
              : ''
          )
          .filter(Boolean)
          .join('\n')
      : '',
  }
}

function buildManualMetadata(
  fields: ReturnType<typeof manualFieldsFromValue>,
  originalValue: BookMetadataValue | null = null
): BookMetadataValue {
  const splitComma = (s: string): string[] =>
    s
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean)

  const parseTerminology = (s: string) =>
    s
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const eqIdx = line.indexOf('=')
        if (eqIdx === -1) {
          // No '=' → term only (no translation)
          return { term: line.trim() }
        }
        const term = line.slice(0, eqIdx).trim()
        const suggested = line.slice(eqIdx + 1).trim()
        return suggested
          ? { term, suggested_translation: suggested }
          : { term }
      })
      .filter((t) => t.term)

  const preserved: Record<string, unknown> = {}
  if (originalValue) {
    for (const [k, v] of Object.entries(originalValue)) {
      if (k === 'metadata_source' || k === 'metadata_filename') continue
      if (
        k === 'book_metadata' ||
        k === 'content_classification' ||
        k === 'audience_analysis' ||
        k === 'stylistic_analysis' ||
        k === 'translation_guidelines'
      ) {
        continue
      }
      preserved[k] = v
    }
  }

  const out: BookMetadataValue = { metadata_source: 'manual', ...preserved }

  const book: Record<string, string> = {}
  if (fields.title) book.title = fields.title
  if (fields.originalTitle) book.original_title = fields.originalTitle
  if (fields.author) book.author = fields.author
  if (Object.keys(book).length) out.book_metadata = book

  const cc: Record<string, unknown> = {}
  if (fields.primaryGenre) cc.primary_genre = fields.primaryGenre
  const subs = splitComma(fields.subGenres)
  if (subs.length) cc.sub_genres = subs
  const themes = splitComma(fields.mainThemes)
  if (themes.length) cc.main_themes = themes
  const setting: Record<string, string> = {}
  if (fields.timePeriod) setting.time_period = fields.timePeriod
  if (fields.location) setting.location = fields.location
  if (Object.keys(setting).length) cc.setting = setting
  if (Object.keys(cc).length) out.content_classification = cc

  const aa: Record<string, string> = {}
  if (fields.targetAudience) aa.target_audience = fields.targetAudience
  if (fields.readingLevel) aa.reading_level = fields.readingLevel
  if (Object.keys(aa).length) out.audience_analysis = aa

  const sa: Record<string, string> = {}
  if (fields.vocabularyComplexity)
    sa.vocabulary_complexity = fields.vocabularyComplexity
  if (Object.keys(sa).length) out.stylistic_analysis = sa

  const tg: Record<string, unknown> = {}
  if (fields.culturalContext) tg.cultural_context = fields.culturalContext
  const kt = parseTerminology(fields.keyTerminology)
  if (kt.length) tg.key_terminology = kt
  if (Object.keys(tg).length) out.translation_guidelines = tg

  return out
}

// --- Validation --------------------------------------------------------------

const ENGLISH_ONLY_FIELDS = new Set([
  'title',
  'originalTitle',
  'author',
  'primaryGenre',
  'subGenres',
  'mainThemes',
  'timePeriod',
  'location',
  'targetAudience',
  'readingLevel',
  'vocabularyComplexity',
  'culturalContext',
])

function validateKeyTerminology(text: string): string | null {
  const lines = text.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    const eqIdx = line.indexOf('=')
    const termPart =
      eqIdx === -1 ? line.trim() : line.slice(0, eqIdx).trim()

    if (!termPart) {
      return `Line ${i + 1}: term is empty.`
    }
    if (!containsLatin(termPart)) {
      return `Line ${i + 1}: term must be in English.`
    }
  }
  return null
}

// --- Field row components ----------------------------------------------------

interface FieldProps {
  fieldKey: keyof ReturnType<typeof manualFieldsFromValue>
  label: string
  value: string
  onChange: (v: string) => void
  placeholder: string
  tooltip: string
  help: string
  error?: string
  multiline?: boolean
  textareaRows?: number
  fullWidth?: boolean
}

function MetadataField({
  fieldKey,
  label,
  value,
  onChange,
  placeholder,
  tooltip,
  help,
  error,
  multiline,
  textareaRows = 2,
  fullWidth,
}: FieldProps) {
  return (
    <div className={cn('space-y-1.5', fullWidth && 'sm:col-span-2')}>
      <Label htmlFor={`meta-${fieldKey}`}>
        <Tooltip content={tooltip}>
          <span className="cursor-help">{label} ⓘ</span>
        </Tooltip>
      </Label>
      {multiline ? (
        <Textarea
          id={`meta-${fieldKey}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={textareaRows}
          aria-invalid={!!error}
        />
      ) : (
        <Input
          id={`meta-${fieldKey}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-invalid={!!error}
        />
      )}
      <p
        className="text-[11px] italic"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        {help}
      </p>
      {error && (
        <p className="text-xs" style={{ color: 'rgb(var(--color-error))' }}>
          {error}
        </p>
      )}
    </div>
  )
}

// --- Component --------------------------------------------------------------

export function BookMetadataPanel({
  value,
  onChange,
  isSaving = false,
  defaultCollapsed = true,
}: Props) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(!defaultCollapsed)
  const [tab, setTab] = useState<'manual' | 'json'>('manual')
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [jsonFileName, setJsonFileName] = useState<string | null>(null)
  const [fields, setFields] = useState(manualFieldsFromValue(value))
  const [dirty, setDirty] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const fileInputRef = useRef<HTMLInputElement>(null)

  const source = detectSource(value)

  useEffect(() => {
    if (!dirty) {
      setFields(manualFieldsFromValue(value))
      if (
        value?.metadata_filename &&
        typeof value.metadata_filename === 'string'
      ) {
        setJsonFileName(value.metadata_filename)
      }
      if (source === 'json') setTab('json')
      else if (source === 'manual') setTab('manual')
    }
  }, [value, dirty, source])

  const setField = <K extends keyof typeof fields>(
    key: K,
    val: (typeof fields)[K]
  ) => {
    const strVal = String(val)
    if (ENGLISH_ONLY_FIELDS.has(key as string) && containsPersian(strVal)) {
      setFieldErrors((prev) => ({
        ...prev,
        [key]: t('metadata.englishOnly'),
      }))
    } else if (key === 'keyTerminology') {
      const err = validateKeyTerminology(strVal)
      setFieldErrors((prev) => {
        const next = { ...prev }
        if (err) next[key] = err
        else delete next[key]
        return next
      })
    } else {
      setFieldErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }
    setFields((prev) => ({ ...prev, [key]: val }))
    setDirty(true)
  }

  const hasAnyError = Object.keys(fieldErrors).length > 0

  const handleManualSave = () => {
    if (hasAnyError) return
    const meta = buildManualMetadata(fields, value)
    if (Object.keys(meta).length <= 1) {
      onChange(null)
    } else {
      onChange(meta)
    }
    setDirty(false)
  }

  const handleJsonFile = useCallback(
    async (file: File) => {
      setJsonError(null)
      if (!file.name.toLowerCase().endsWith('.json')) {
        setJsonError(t('metadata.jsonMustBeJson'))
        return
      }
      try {
        const text = await file.text()
        const parsed = JSON.parse(text)
        if (
          typeof parsed !== 'object' ||
          parsed === null ||
          Array.isArray(parsed)
        ) {
          setJsonError(t('metadata.jsonMustBeObject'))
          return
        }
        const withSource: BookMetadataValue = {
          ...parsed,
          metadata_source: 'json',
          metadata_filename: file.name,
        }
        setJsonFileName(file.name)
        onChange(withSource)
      } catch (err) {
        setJsonError(
          `${t('metadata.jsonParseError')}: ${(err as Error).message}`
        )
      }
    },
    [onChange, t]
  )

  const handleClear = () => {
    setFields(manualFieldsFromValue(null))
    setJsonFileName(null)
    setJsonError(null)
    setFieldErrors({})
    setDirty(false)
    onChange(null)
  }

  const isEmpty =
    !value ||
    Object.keys(value).filter(
      (k) => k !== 'metadata_source' && k !== 'metadata_filename'
    ).length === 0
  const summary = isEmpty
    ? t('metadata.none')
    : source === 'json'
    ? t('metadata.sourceJson', {
        name: jsonFileName || value?.metadata_filename || 'JSON',
      })
    : t('metadata.sourceManual')

  return (
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
        <div className="flex items-center gap-2 min-w-0">
          <FileJson
            className="h-4 w-4 shrink-0"
            style={{ color: 'rgb(var(--color-primary))' }}
          />
          <div className="min-w-0">
            <div className="text-sm font-semibold">
              {t('metadata.title')}
            </div>
            <div
              className="text-xs truncate"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              {summary}
            </div>
          </div>
        </div>
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 transition-transform',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div
          className="border-t p-4 space-y-4 rg-anim-fade-up"
          style={{ borderColor: 'rgb(var(--color-border))' }}
        >
          <Tabs
            value={tab}
            onValueChange={async (v) => {
              if (dirty && tab !== v) {
                const ok = await new Promise<boolean>((resolve) => {
                  // Use browser confirm for simplicity here to avoid extra coupling.
                  resolve(
                    window.confirm(t('confirm.unsavedChanges.description'))
                  )
                })
                if (!ok) return
                setDirty(false)
                setFieldErrors({})
              }
              setTab(v as 'manual' | 'json')
            }}
          >
            <TabsList>
              <TabsTrigger value="manual">
                <FormInput className="h-3.5 w-3.5 me-1" />
                {t('metadata.tabManual')}
              </TabsTrigger>
              <TabsTrigger value="json">
                <Upload className="h-3.5 w-3.5 me-1" />
                {t('metadata.tabJson')}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="manual">
              <div className="space-y-4">
                {source === 'json' && (
                  <div
                    className="rounded-md border p-2 text-xs"
                    style={{
                      borderColor: 'rgb(var(--color-warning))',
                      color: 'rgb(var(--color-warning))',
                      backgroundColor: 'rgb(var(--color-surface-alt))',
                    }}
                  >
                    {t('metadata.manualOverridesJson')}
                  </div>
                )}

                <div
                  className="rounded-md border p-2 text-xs"
                  style={{
                    borderColor: 'rgb(var(--color-info))',
                    backgroundColor: 'rgb(var(--color-surface-alt))',
                    color: 'rgb(var(--color-text-muted))',
                  }}
                >
                  {t('metadata.englishRequired')}
                </div>

                {/* Book Info */}
                <section className="space-y-3">
                  <h4 className="text-sm font-semibold">
                    {t('metadata.sectionBook')}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <MetadataField
                      fieldKey="title"
                      label={t('metadata.fields.title')}
                      value={fields.title}
                      onChange={(v) => setField('title', v)}
                      placeholder={t('metadata.placeholders.title')}
                      tooltip={t('metadata.fieldTooltips.title')}
                      help={t('metadata.fieldHelp.title')}
                      error={fieldErrors.title}
                    />
                    <MetadataField
                      fieldKey="originalTitle"
                      label={t('metadata.fields.originalTitle')}
                      value={fields.originalTitle}
                      onChange={(v) => setField('originalTitle', v)}
                      placeholder={t('metadata.placeholders.originalTitle')}
                      tooltip={t('metadata.fieldTooltips.originalTitle')}
                      help={t('metadata.fieldHelp.originalTitle')}
                      error={fieldErrors.originalTitle}
                    />
                    <MetadataField
                      fieldKey="author"
                      label={t('metadata.fields.author')}
                      value={fields.author}
                      onChange={(v) => setField('author', v)}
                      placeholder={t('metadata.placeholders.author')}
                      tooltip={t('metadata.fieldTooltips.author')}
                      help={t('metadata.fieldHelp.author')}
                      error={fieldErrors.author}
                      fullWidth
                    />
                  </div>
                </section>

                {/* Classification */}
                <section className="space-y-3">
                  <h4 className="text-sm font-semibold">
                    {t('metadata.sectionClassification')}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <MetadataField
                      fieldKey="primaryGenre"
                      label={t('metadata.fields.primaryGenre')}
                      value={fields.primaryGenre}
                      onChange={(v) => setField('primaryGenre', v)}
                      placeholder={t('metadata.placeholders.primaryGenre')}
                      tooltip={t('metadata.fieldTooltips.primaryGenre')}
                      help={t('metadata.fieldHelp.primaryGenre')}
                      error={fieldErrors.primaryGenre}
                    />
                    <MetadataField
                      fieldKey="subGenres"
                      label={t('metadata.fields.subGenres')}
                      value={fields.subGenres}
                      onChange={(v) => setField('subGenres', v)}
                      placeholder={t('metadata.placeholders.subGenres')}
                      tooltip={t('metadata.fieldTooltips.subGenres')}
                      help={t('metadata.fieldHelp.subGenres')}
                      error={fieldErrors.subGenres}
                    />
                    <MetadataField
                      fieldKey="mainThemes"
                      label={t('metadata.fields.mainThemes')}
                      value={fields.mainThemes}
                      onChange={(v) => setField('mainThemes', v)}
                      placeholder={t('metadata.placeholders.mainThemes')}
                      tooltip={t('metadata.fieldTooltips.mainThemes')}
                      help={t('metadata.fieldHelp.mainThemes')}
                      error={fieldErrors.mainThemes}
                      fullWidth
                    />
                    <MetadataField
                      fieldKey="timePeriod"
                      label={t('metadata.fields.timePeriod')}
                      value={fields.timePeriod}
                      onChange={(v) => setField('timePeriod', v)}
                      placeholder={t('metadata.placeholders.timePeriod')}
                      tooltip={t('metadata.fieldTooltips.timePeriod')}
                      help={t('metadata.fieldHelp.timePeriod')}
                      error={fieldErrors.timePeriod}
                    />
                    <MetadataField
                      fieldKey="location"
                      label={t('metadata.fields.location')}
                      value={fields.location}
                      onChange={(v) => setField('location', v)}
                      placeholder={t('metadata.placeholders.location')}
                      tooltip={t('metadata.fieldTooltips.location')}
                      help={t('metadata.fieldHelp.location')}
                      error={fieldErrors.location}
                    />
                  </div>
                </section>

                {/* Audience */}
                <section className="space-y-3">
                  <h4 className="text-sm font-semibold">
                    {t('metadata.sectionAudience')}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <MetadataField
                      fieldKey="targetAudience"
                      label={t('metadata.fields.targetAudience')}
                      value={fields.targetAudience}
                      onChange={(v) => setField('targetAudience', v)}
                      placeholder={t('metadata.placeholders.targetAudience')}
                      tooltip={t('metadata.fieldTooltips.targetAudience')}
                      help={t('metadata.fieldHelp.targetAudience')}
                      error={fieldErrors.targetAudience}
                    />
                    <MetadataField
                      fieldKey="readingLevel"
                      label={t('metadata.fields.readingLevel')}
                      value={fields.readingLevel}
                      onChange={(v) => setField('readingLevel', v)}
                      placeholder={t('metadata.placeholders.readingLevel')}
                      tooltip={t('metadata.fieldTooltips.readingLevel')}
                      help={t('metadata.fieldHelp.readingLevel')}
                      error={fieldErrors.readingLevel}
                    />
                    <MetadataField
                      fieldKey="vocabularyComplexity"
                      label={t('metadata.fields.vocabularyComplexity')}
                      value={fields.vocabularyComplexity}
                      onChange={(v) => setField('vocabularyComplexity', v)}
                      placeholder={t(
                        'metadata.placeholders.vocabularyComplexity'
                      )}
                      tooltip={t(
                        'metadata.fieldTooltips.vocabularyComplexity'
                      )}
                      help={t('metadata.fieldHelp.vocabularyComplexity')}
                      error={fieldErrors.vocabularyComplexity}
                    />
                  </div>
                </section>

                {/* Translation Guidelines */}
                <section className="space-y-3">
                  <h4 className="text-sm font-semibold">
                    {t('metadata.sectionTranslation')}
                  </h4>
                  <MetadataField
                    fieldKey="culturalContext"
                    label={t('metadata.fields.culturalContext')}
                    value={fields.culturalContext}
                    onChange={(v) => setField('culturalContext', v)}
                    placeholder={t('metadata.placeholders.culturalContext')}
                    tooltip={t('metadata.fieldTooltips.culturalContext')}
                    help={t('metadata.fieldHelp.culturalContext')}
                    error={fieldErrors.culturalContext}
                    multiline
                    textareaRows={2}
                  />
                  <MetadataField
                    fieldKey="keyTerminology"
                    label={t('metadata.fields.keyTerminology')}
                    value={fields.keyTerminology}
                    onChange={(v) => setField('keyTerminology', v)}
                    placeholder={t('metadata.placeholders.keyTerminology')}
                    tooltip={t('metadata.fieldTooltips.keyTerminology')}
                    help={t('metadata.fieldHelp.keyTerminology')}
                    error={fieldErrors.keyTerminology}
                    multiline
                    textareaRows={3}
                  />
                </section>

                <div className="flex flex-wrap gap-2 pt-2">
                  <Button
                    onClick={handleManualSave}
                    disabled={!dirty || isSaving || hasAnyError}
                  >
                    {isSaving ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {t('common.save')}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={handleClear}
                    disabled={isSaving || isEmpty}
                  >
                    <Trash2
                      className="h-4 w-4"
                      style={{ color: 'rgb(var(--color-error))' }}
                    />
                    {t('metadata.clear')}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="json">
              <div className="space-y-4">
                {source === 'json' ? (
                  <div
                    className="rounded-md border p-3 text-sm flex items-start justify-between gap-3"
                    style={{
                      borderColor: 'rgb(var(--color-success))',
                      backgroundColor: 'rgb(var(--color-surface-alt))',
                    }}
                  >
                    <div>
                      <div
                        className="font-medium"
                        style={{ color: 'rgb(var(--color-success))' }}
                      >
                        ✓ {t('metadata.jsonLoaded')}
                      </div>
                      <div
                        className="text-xs mt-1"
                        style={{ color: 'rgb(var(--color-text-muted))' }}
                      >
                        {jsonFileName ||
                          value?.metadata_filename ||
                          'metadata.json'}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClear}
                      disabled={isSaving}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {t('metadata.clear')}
                    </Button>
                  </div>
                ) : (
                  <>
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 cursor-pointer transition-colors"
                      style={{
                        backgroundColor: 'rgb(var(--color-surface))',
                        borderColor: 'rgb(var(--color-border))',
                      }}
                    >
                      <FileUp
                        className="h-8 w-8 mb-2"
                        style={{ color: 'rgb(var(--color-text-muted))' }}
                      />
                      <p className="text-sm font-medium">
                        {t('metadata.jsonDropzone')}
                      </p>
                      <p
                        className="text-xs mt-1"
                        style={{ color: 'rgb(var(--color-text-muted))' }}
                      >
                        {t('metadata.jsonDropzoneHint')}
                      </p>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".json,application/json"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) handleJsonFile(f)
                        e.target.value = ''
                      }}
                    />
                  </>
                )}

                {jsonError && (
                  <div
                    className="flex items-start gap-2 rounded-md border p-2 text-xs"
                    style={{
                      borderColor: 'rgb(var(--color-error))',
                      color: 'rgb(var(--color-error))',
                    }}
                  >
                    <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                    <span>{jsonError}</span>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}