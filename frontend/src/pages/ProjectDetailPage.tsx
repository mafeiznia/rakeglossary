import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  ArrowLeft,
  RefreshCw,
  Loader2,
  Square,
  FolderOpen,
  Sparkles,
} from 'lucide-react'
import { toast } from 'sonner'
import { Tooltip } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { ProgressLog } from '@/features/progress/components/ProgressLog'
import { useProgressStream } from '@/features/progress/hooks/useProgressStream'
import { GlossaryTable } from '@/features/glossary/components/GlossaryTable'
import { GlossaryTableSkeleton } from '@/features/glossary/components/GlossaryTableSkeleton'
import { useGlossary } from '@/features/glossary/hooks/useGlossary'
import { ExportButtons } from '@/features/projects/components/ExportButtons'
import { OptionsPanel } from '@/features/projects/components/OptionsPanel'
import { useProject } from '@/features/projects/hooks/useProject'
import { SourcesPanel } from '@/features/sources/components/SourcesPanel'
import { useStopwords } from '@/features/settings/hooks/useStopwords'
import {
  BookMetadataPanel,
  type BookMetadataValue,
} from '@/features/metadata/components/BookMetadataPanel'
import { useConfirm } from '@/features/confirm/confirmStore'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/empty-state'
import { projectsApi } from '@/api'
import type { ProcessRequest } from '@/types'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'Pending', color: 'rgb(var(--color-text-muted))' },
  processing: { label: 'Processing...', color: 'rgb(var(--color-info))' },
  done: { label: 'Done', color: 'rgb(var(--color-success))' },
  failed: { label: 'Failed', color: 'rgb(var(--color-error))' },
  cancelled: { label: 'Cancelled', color: 'rgb(var(--color-warning))' },
}

export function ProjectDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const confirm = useConfirm()

  const {
    data: project,
    isLoading,
    isError,
    reprocess,
    isReprocessing,
    cancel,
    isCancelling,
  } = useProject(id)
  
  const glossary = useGlossary(id)
  const stopwords = useStopwords()

  const isLive = project?.status === 'processing'
  const { events, connected } = useProgressStream(id, !!isLive)

  const [showOptions, setShowOptions] = useState(false)
  const optionsRef = useRef<HTMLDivElement>(null)

  const [options, setOptions] = useState<ProcessRequest>({
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
  })

  const [optionsInitialized, setOptionsInitialized] = useState(false)
  useEffect(() => {
    if (!project || optionsInitialized) return
    setOptions({
      num_terms: project.num_terms,
      terms_per_1k_words: project.terms_per_1k_words,
      translate_terms: project.translate_terms,
      translate_definitions: project.translate_definitions,
      translation_provider: project.translation_provider,
      processing_mode: project.processing_mode,
      use_spacy: project.use_spacy,
      use_rake: project.use_rake,
      use_yake: project.use_yake,
      use_ner: project.use_ner,
    })
    setOptionsInitialized(true)
  }, [project, optionsInitialized])

  // Remember last project visited so Settings can return here
  useEffect(() => {
    if (project?.id) {
      try {
        localStorage.setItem('lastProjectId', project.id)
      } catch {
        // ignore
      }
    }
  }, [project?.id])

  useEffect(() => {
    if (!isError) return
    const timer = setTimeout(() => {
      navigate('/projects', { replace: true })
    }, 5000)
    return () => clearTimeout(timer)
  }, [isError, navigate])

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="space-y-3">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-3">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
        <GlossaryTableSkeleton rows={8} />
      </div>
    )
  }

  if (isError || !project) {
    return (
      <div className="max-w-2xl mx-auto py-16">
        <EmptyState
          icon={FolderOpen}
          title={t('projectDetail.notFoundTitle')}
          description={t('projectDetail.notFoundDesc')}
          actionLabel={t('projectDetail.backToProjects')}
          onAction={() => navigate('/projects', { replace: true })}
        />
      </div>
    )
  }

  const status = STATUS_LABELS[project.status] || STATUS_LABELS.pending
  const processing = project.status === 'processing'
  const hasEntries = (glossary.data?.entries?.length ?? 0) > 0
  const hasIncludedSources =
    project.sources.filter((s) => s.included).length > 0

  const openOptionsAndScroll = () => {
    setShowOptions(true)
    setTimeout(() => {
      optionsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',      // ← تغییر از 'center' به 'start'
      })
      // Fallback: also scroll the main container to top
      const main = document.querySelector('main')
      if (main) {
        main.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }, 200)
  }

  const handleReprocess = async () => {
    try {
      await reprocess(options)
      setShowOptions(false)
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const handleCancel = async () => {
    const ok = await confirm({
      title: t('confirm.stopProcessing.title'),
      description: t('confirm.stopProcessing.description'),
      confirmLabel: t('common.confirm'),
      variant: 'destructive',
    })
    if (!ok) return
    try {
      await cancel()
      toast.success(t('toast.processingCancelled'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const handleDeleteEntry = async (entryId: number) => {
    const ok = await confirm({
      title: t('confirm.deleteEntry.title'),
      description: t('confirm.deleteEntry.description'),
      confirmLabel: t('common.delete'),
      variant: 'destructive',
    })
    if (!ok) return
    try {
      await glossary.remove(entryId)
      toast.success(t('toast.entryDeleted'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const handleBlacklist = async (term: string, entryId: number) => {
    const ok = await confirm({
      title: t('confirm.blacklist.title'),
      description: t('confirm.blacklist.description', { term }),
      confirmLabel: t('common.confirm'),
      variant: 'destructive',
    })
    if (!ok) return
    try {
      await stopwords.add(term)
      await glossary.remove(entryId)
      toast.success(t('toast.blacklistAdded'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const handleMetadataChange = async (meta: BookMetadataValue | null) => {
    try {
      if (meta === null) {
        await projectsApi.clearMetadata(project.id)
        toast.success(t('toast.metadataCleared'))
      } else {
        await projectsApi.updateMetadata(project.id, meta)
        toast.success(t('toast.saved'))
      }
      qc.invalidateQueries({ queryKey: ['project', project.id] })
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Tooltip content="بازگشت به لیست پروژه‌ها">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/projects')}
              className="mb-2 -ms-2"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Projects
            </Button>
          </Tooltip>
          <h2 className="text-2xl font-bold truncate">{project.title}</h2>
          <div className="flex items-center gap-3 mt-1 text-sm">
            <span
              className="flex items-center gap-1.5"
              style={{ color: status.color }}
            >
              {processing && <Loader2 className="h-3 w-3 animate-spin" />}
              {status.label}
            </span>
            <span style={{ color: 'rgb(var(--color-text-muted))' }}>
              · {project.word_count.toLocaleString()} words
            </span>
            <span style={{ color: 'rgb(var(--color-text-muted))' }}>
              · {project.source_count} sources
            </span>
            <span style={{ color: 'rgb(var(--color-text-muted))' }}>
              · {project.num_terms} max terms
            </span>
            <span
              className="px-2 py-0.5 rounded text-xs"
              style={{
                backgroundColor: 'rgb(var(--color-surface-alt))',
                color: 'rgb(var(--color-text-muted))',
              }}
            >
              mode: {project.processing_mode}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {processing ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={isCancelling}
            >
              {isCancelling ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Square className="h-3.5 w-3.5" />
              )}
              Stop
            </Button>
          ) : (
            <>
              {hasEntries && <ExportButtons projectId={project.id} />}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (showOptions) {
                    setShowOptions(false)
                  } else {
                    openOptionsAndScroll()
                  }
                }}
                disabled={isReprocessing || !hasIncludedSources}
                title={
                  !hasIncludedSources
                    ? 'Add at least one source first'
                    : undefined
                }
              >
                <RefreshCw className="h-3.5 w-3.5" />
                {hasEntries ? 'Re-process' : 'Process'}
              </Button>
            </>
          )}
        </div>
      </div>

      {project.error_message && (
        <div
          className="rounded-lg border p-4 text-sm"
          style={{
            borderColor: 'rgb(var(--color-error))',
            color: 'rgb(var(--color-error))',
            backgroundColor: 'rgb(var(--color-surface))',
          }}
        >
          {project.error_message}
        </div>
      )}

      <BookMetadataPanel
        value={(project.book_metadata as BookMetadataValue) || null}
        onChange={handleMetadataChange}
        defaultCollapsed={true}
      />

      <SourcesPanel projectId={project.id} />

      {showOptions && (
        <div ref={optionsRef} className="space-y-3">
          <OptionsPanel
            options={options}
            onChange={setOptions}
            defaultOpen={true}
          />
          <div className="flex gap-2">
            <Button onClick={handleReprocess} disabled={isReprocessing}>
              {isReprocessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Start processing
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowOptions(false)}
              disabled={isReprocessing}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {(processing || events.length > 0) && (
        <ProgressLog events={events} connected={connected} />
      )}

      {glossary.isLoading ? (
        <GlossaryTableSkeleton rows={8} />
      ) : hasEntries ? (
        <GlossaryTable
          entries={glossary.data!.entries}
          onUpdate={async (entryId, patch) => {
            await glossary.update({ entryId, payload: patch })
          }}
          onDelete={handleDeleteEntry}
          onBlacklist={handleBlacklist}
        />
      ) : (
        !processing &&
        hasIncludedSources && (
          <EmptyState
            icon={Sparkles}
            title={t('projectDetail.noGlossaryTitle')}
            description={t('projectDetail.noGlossaryDesc')}
            actionLabel={t('projectDetail.processNow')}
            onAction={openOptionsAndScroll}
          />
        )
      )}
    </div>
  )
}