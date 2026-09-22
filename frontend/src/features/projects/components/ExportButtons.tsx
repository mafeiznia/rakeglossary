import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { exportApi } from '@/api'
import type { ExportFormat } from '@/types'

interface Props {
  projectId: string
}

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: 'csv', label: 'CSV' },
  { value: 'xlsx', label: 'Excel' },
  { value: 'tbx', label: 'TBX' },
]

export function ExportButtons({ projectId }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {FORMATS.map(({ value, label }) => (
        <a
          key={value}
          href={exportApi.downloadUrl(projectId, value)}
          download
        >
          <Button variant="outline" size="sm">
            <Download className="h-3.5 w-3.5" />
            {label}
          </Button>
        </a>
      ))}
    </div>
  )
}