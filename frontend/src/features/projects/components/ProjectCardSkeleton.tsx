import { Skeleton } from '@/components/ui/skeleton'

export function ProjectCardSkeleton() {
  return (
    <div
      className="rounded-lg border p-4 flex flex-col gap-3"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      {/* Title */}
      <Skeleton className="h-5 w-3/4" />

      {/* Meta */}
      <div className="flex gap-3">
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-14" />
      </div>

      {/* Status + date */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  )
}