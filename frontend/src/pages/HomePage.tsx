import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  AlertCircle,
  FileText,
  Loader2,
  Sparkles,
  Type,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { projectsApi, sourcesApi } from '@/api'
import { llmApi } from '@/api/llm'
import { MultiFileDropzone } from '@/features/sources/components/MultiFileDropzone'
import {
  BookMetadataPanel,
  type BookMetadataValue,
} from '@/features/metadata/components/BookMetadataPanel'
import type { ProcessingMode, ProcessRequest } from '@/types'

const DEFAULT_OPTIONS: ProcessRequest = {
  num_terms: 500,
  terms_per_1k_words: 15.0,
  translate_terms: true,
  translate_definitions: true,
  translation_provider: 'argos',
  processing_mode: 'offline',
  use_spacy: true,
  use_rake: true,
  use_yake: true,
  use_ner: true,
}

export function HomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [title, setTitle] = useState('')
  const [sourceTab, setSourceTab] = useState<'file' | 'text'>('file')
  const [files, setFiles] = useState<File[]>([])
  const [textName, setTextName] = useState('')
  const [textBody, setTextBody] = useState('')
  const [metadata, setMetadata] = useState<BookMetadataValue | null>(null)
  const [busy, setBusy] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null)

  const llmConfigQuery = useQuery({
    queryKey: ['llm', 'config'],
    queryFn: llmApi.getConfig,
    staleTime: 30_000,
  })
  const llmReady = Boolean(
    llmConfigQuery.data?.enabled && llmConfigQuery.data?.has_api_key
  )

  const [processingMode, setProcessingMode] = useState<ProcessingMode>('offline')

  useEffect(() => {
    if (llmConfigQuery.data) {
      setProcessingMode(llmReady ? 'hybrid' : 'offline')
    }
  }, [llmConfigQuery.data, llmReady])

  const handleFiles = (newFiles: File[]) => {
    setDuplicateWarning(null)
    const rejected: string[] = []

    setFiles((prev) => {
      const existing = new Set(
        prev.map((f) => `${f.name.toLowerCase()}::${f.size}`)
      )
      const additions: File[] = []
      const seenInBatch = new Set<string>()

      for (const f of newFiles) {
        const key = `${f.name.toLowerCase()}::${f.size}`
        if (existing.has(key) || seenInBatch.has(key)) {
          rejected.push(f.name)
          continue
        }
        seenInBatch.add(key)
        additions.push(f)
      }

      if (rejected.length > 0) {
        setDuplicateWarning(
          `${rejected.join(', ')} — ${t('home.duplicateWarning')}`
        )
      }

      return [...prev, ...additions]
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!title.trim()) {
      setLocalError(t('home.errorEmptyTitle'))
      return
    }

    const hasFile = files.length > 0
    const hasText = Boolean(textName.trim() && textBody.trim())
    const hasSource =
      (sourceTab === 'file' && hasFile) || (sourceTab === 'text' && hasText)

    setBusy(true)
    try {
      const project = await projectsApi.createEmpty({
        title: title.trim(),
        num_terms: DEFAULT_OPTIONS.num_terms,
        terms_per_1k_words: DEFAULT_OPTIONS.terms_per_1k_words,
        translate_terms: DEFAULT_OPTIONS.translate_terms,
        translate_definitions: DEFAULT_OPTIONS.translate_definitions,
        translation_provider: DEFAULT_OPTIONS.translation_provider,
        processing_mode: processingMode,
        use_spacy: DEFAULT_OPTIONS.use_spacy,
        use_rake: DEFAULT_OPTIONS.use_rake,
        use_yake: DEFAULT_OPTIONS.use_yake,
        use_ner: DEFAULT_OPTIONS.use_ner,
      })

      if (metadata) {
        try {
          await projectsApi.updateMetadata(project.id, metadata)
        } catch (metaErr) {
          console.warn('Failed to attach metadata:', metaErr)
          toast.warning(
            `${t('toast.uploadFailedTitle')}: metadata — ${(metaErr as Error).message}`
          )
        }
      }

      if (hasSource) {
        try {
          if (sourceTab === 'file' && files.length > 0) {
            await sourcesApi.uploadFiles(project.id, files)
          } else if (sourceTab === 'text' && hasText) {
            await sourcesApi.addText(project.id, {
              name: textName.trim(),
              text: textBody,
            })
          }
        } catch (uploadErr) {
          const msg = (uploadErr as Error).message
          toast.warning(
            `${t('toast.uploadFailedTitle')}: ${t('toast.uploadFailedDesc')} — ${msg}`
          )
        }
      }

      toast.success(t('toast.saved'))
      navigate(`/projects/${project.id}`)
    } catch (err) {
      setLocalError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const hasFile = files.length > 0
  const hasText = Boolean(textName.trim() && textBody.trim())
  const hasSource =
    (sourceTab === 'file' && hasFile) || (sourceTab === 'text' && hasText)

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{t('home.title')}</h2>
        <p
          className="mt-1 text-sm"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          {t('home.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">{t('home.titleLabel')}</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t('home.titlePlaceholder')}
            disabled={busy}
            maxLength={255}
          />
        </div>

        <div className="space-y-2">
          <p
            className="text-xs"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {t('home.sourceOptionalHint')}
          </p>
          <Tabs
            value={sourceTab}
            onValueChange={(v) => setSourceTab(v as 'file' | 'text')}
          >
            <TabsList>
              <TabsTrigger value="file">
                <FileText className="h-3.5 w-3.5 me-1" />
                {t('home.sourceTabFile')}
              </TabsTrigger>
              <TabsTrigger value="text">
                <Type className="h-3.5 w-3.5 me-1" />
                {t('home.sourceTabText')}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="file">
              <div className="space-y-2">
                <MultiFileDropzone onFiles={handleFiles} disabled={busy} />

                {duplicateWarning && (
                  <div
                    className="flex items-start gap-2 rounded-md border p-2 text-xs"
                    style={{
                      borderColor: 'rgb(var(--color-warning))',
                      color: 'rgb(var(--color-warning))',
                      backgroundColor: 'rgb(var(--color-surface))',
                    }}
                  >
                    <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                    <span>{duplicateWarning}</span>
                  </div>
                )}

                {files.length > 0 && (
                  <div className="space-y-1 mt-2">
                    {files.map((f, i) => (
                      <div
                        key={`${f.name}-${i}`}
                        className="flex items-center justify-between rounded border px-3 py-1.5 text-sm"
                        style={{
                          borderColor: 'rgb(var(--color-border))',
                          backgroundColor: 'rgb(var(--color-surface))',
                        }}
                      >
                        <span className="truncate">
                          {f.name}{' '}
                          <span
                            className="text-xs"
                            style={{ color: 'rgb(var(--color-text-muted))' }}
                          >
                            ({(f.size / 1024).toFixed(1)} KB)
                          </span>
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            setFiles((prev) => prev.filter((_, j) => j !== i))
                          }
                          className="text-xs ms-2 hover:opacity-70"
                          style={{ color: 'rgb(var(--color-error))' }}
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="text">
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="text-name">{t('home.textName')}</Label>
                  <Input
                    id="text-name"
                    value={textName}
                    onChange={(e) => setTextName(e.target.value)}
                    placeholder={t('home.textNamePlaceholder')}
                    maxLength={255}
                    disabled={busy}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="text-body">{t('home.textBody')}</Label>
                  <Textarea
                    id="text-body"
                    value={textBody}
                    onChange={(e) => setTextBody(e.target.value)}
                    placeholder={t('home.textBodyPlaceholder')}
                    rows={12}
                    disabled={busy}
                  />
                  <p
                    className="text-xs"
                    style={{ color: 'rgb(var(--color-text-muted))' }}
                  >
                    {t('home.textStats', {
                      words: textBody.trim()
                        ? textBody.trim().split(/\s+/).length
                        : 0,
                      chars: textBody.length,
                    })}
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        <BookMetadataPanel
          value={metadata}
          onChange={setMetadata}
          defaultCollapsed={true}
        />

        {localError && (
          <div
            className="rounded-md border p-3 text-sm"
            style={{
              borderColor: 'rgb(var(--color-error))',
              color: 'rgb(var(--color-error))',
            }}
          >
            {localError}
          </div>
        )}

        <div className="flex gap-2">
          <Button type="submit" size="lg" disabled={busy}>
            {busy ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {t('home.submitting')}
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                {hasSource ? t('home.submit') : t('home.createProjectOnly')}
              </>
            )}
          </Button>
        </div>

        <p
          className="text-xs"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          {t('home.afterCreateHint')}
        </p>
      </form>
    </div>
  )
}