import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  FileText,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  XCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ProjectSummary, ProjectStatus } from '@/types'

interface Props {
  project: ProjectSummary
  onDelete: (id: string) => void
  isDeleting: boolean
}

const STATUS_META: Record<
  ProjectStatus,
  { icon: typeof CheckCircle2; color: string; labelKey: string }
> = {
  pending: {
    icon: Clock,
    color: 'rgb(var(--color-text-muted))',
    labelKey: 'projects.statusPending',
  },
  processing: {
    icon: Loader2,
    color: 'rgb(var(--color-info))',
    labelKey: 'projects.statusProcessing',
  },
  done: {
    icon: CheckCircle2,
    color: 'rgb(var(--color-success))',
    labelKey: 'projects.statusDone',
  },
  failed: {
    icon: AlertCircle,
    color: 'rgb(var(--color-error))',
    labelKey: 'projects.statusFailed',
  },
  cancelled: {
    icon: XCircle,
    color: 'rgb(var(--color-warning))',
    labelKey: 'projects.statusCancelled',
  },
}

export function ProjectCard({ project, onDelete, isDeleting }: Props) {
  const { t } = useTranslation()
  const meta = STATUS_META[project.status]
  const Icon = meta.icon
  const isSpinning = project.status === 'processing'

  const created = new Date(project.created_at).toLocaleString()

  return (
    <div
      className="rounded-lg border p-4 flex flex-col gap-3 transition-shadow hover:shadow-md"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      {/* Title + delete */}
      <div className="flex items-start justify-between gap-2">
        <Link
          to={`/projects/${project.id}`}
          className="flex-1 min-w-0 group"
        >
          <h3 className="font-semibold text-base truncate group-hover:underline">
            {project.title}
          </h3>
        </Link>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 shrink-0"
          onClick={() => onDelete(project.id)}
          disabled={isDeleting}
          title={t('common.delete')}
        >
          {isDeleting ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2
              className="h-3.5 w-3.5"
              style={{ color: 'rgb(var(--color-error))' }}
            />
          )}
        </Button>
      </div>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-3 text-xs" style={{ color: 'rgb(var(--color-text-muted))' }}>
        <span className="flex items-center gap-1">
          <FileText className="h-3.5 w-3.5" />
          {project.source_count} source{project.source_count === 1 ? '' : 's'}
        </span>
        <span>{project.word_count.toLocaleString()} words</span>
        <span>{project.num_terms} terms</span>
      </div>

      {/* Status + created */}
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5" style={{ color: meta.color }}>
          <Icon className={`h-3.5 w-3.5 ${isSpinning ? 'animate-spin' : ''}`} />
          {t(meta.labelKey)}
        </span>
        <span style={{ color: 'rgb(var(--color-text-muted))' }}>
          {created}
        </span>
      </div>
    </div>
  )
}