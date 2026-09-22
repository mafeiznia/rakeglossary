import { Skeleton } from '@/components/ui/skeleton'

interface Props {
  rows?: number
}

export function GlossaryTableSkeleton({ rows = 8 }: Props) {
  return (
    <div
      className="rounded-lg border overflow-hidden"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr
              className="border-b"
              style={{ borderColor: 'rgb(var(--color-border))' }}
            >
              <th className="text-center p-3" style={{ width: '3rem' }}>
                <Skeleton className="h-3 w-4 mx-auto" />
              </th>
              <th className="text-start p-3">
                <Skeleton className="h-3 w-24" />
              </th>
              <th className="text-start p-3">
                <Skeleton className="h-3 w-20" />
              </th>
              <th className="text-start p-3">
                <Skeleton className="h-3 w-16" />
              </th>
              <th className="text-start p-3">
                <Skeleton className="h-3 w-20" />
              </th>
              <th className="text-start p-3" style={{ width: '6rem' }}>
                <Skeleton className="h-3 w-14" />
              </th>
              <th className="text-start p-3" style={{ width: '4rem' }}>
                <Skeleton className="h-3 w-10" />
              </th>
              <th className="text-start p-3" style={{ width: '4rem' }}>
                <Skeleton className="h-3 w-10" />
              </th>
              <th style={{ width: '5rem' }}></th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, i) => (
              <tr
                key={i}
                className="border-b last:border-0"
                style={{ borderColor: 'rgb(var(--color-border))' }}
              >
                <td className="p-3 text-center">
                  <Skeleton className="h-3 w-4 mx-auto" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-20 mt-1.5" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-4 w-24" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-4 w-full max-w-md" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-4 w-full max-w-md" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-5 w-16" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-3 w-10" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-3 w-8" />
                </td>
                <td className="p-3">
                  <Skeleton className="h-6 w-12 ms-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}