import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { FolderOpen, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { useProjectsList } from '@/features/projects/hooks/useProjectsList'
import { ProjectCard } from '@/features/projects/components/ProjectCard'
import { ProjectCardSkeleton } from '@/features/projects/components/ProjectCardSkeleton'
import { useConfirm } from '@/features/confirm/confirmStore'

export function ProjectsPage() {
  const { t } = useTranslation()
  const { data, isLoading, isError, error, remove, isDeleting } =
    useProjectsList()
  const confirm = useConfirm()

  const projects = data?.items ?? []
  const total = data?.total ?? 0

  const handleDelete = async (id: string) => {
    const project = projects.find((p) => p.id === id)
    const ok = await confirm({
      title: t('confirm.deleteProject.title'),
      description: t('confirm.deleteProject.description', {
        title: project?.title ?? id,
      }),
      confirmLabel: t('common.delete'),
      variant: 'destructive',
    })
    if (!ok) return

    try {
      await remove(id)
      toast.success(t('toast.projectDeleted'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">{t('projects.title')}</h2>
          <p
            className="text-sm mt-1"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {total > 0
              ? t('projects.countLabel', { count: total })
              : t('projects.subtitle')}
          </p>
        </div>
        <Link to="/">
          <Button>
            <Plus className="h-4 w-4" />
            {t('projects.newProject')}
          </Button>
        </Link>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ProjectCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error */}
      {isError && (
        <div
          className="rounded-lg border p-6"
          style={{
            borderColor: 'rgb(var(--color-error))',
            color: 'rgb(var(--color-error))',
          }}
        >
          Error: {(error as Error).message}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && projects.length === 0 && (
        <EmptyState
          icon={FolderOpen}
          title={t('projects.empty')}
          description={t('projects.emptyHint')}
          actionLabel={t('projects.newProject')}
          actionHref="/"
        />
      )}

      {/* Grid */}
      {projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onDelete={handleDelete}
              isDeleting={isDeleting}
            />
          ))}
        </div>
      )}
    </div>
  )
}