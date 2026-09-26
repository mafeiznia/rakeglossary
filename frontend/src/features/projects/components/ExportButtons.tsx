import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { exportApi } from '@/api'
import { useAbout } from '@/hooks/useAbout'
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
  const { t } = useTranslation()
  const { data: about } = useAbout()
  const [busy, setBusy] = useState<ExportFormat | null>(null)

  const isDesktop = about?.desktop_mode === true

  const handleDesktopSave = async (format: ExportFormat) => {
    setBusy(format)
    try {
      const res = await exportApi.saveToDownloads(projectId, format)
      if (res.folder_opened) {
        toast.success(
          t('export.savedAndOpened', { filename: res.filename })
        )
      } else {
        toast.success(
          t('export.savedTo', { filename: res.filename, path: res.path })
        )
      }
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setBusy(null)
    }
  }

  if (isDesktop) {
    return (
      <div className="flex flex-wrap gap-2">
        {FORMATS.map(({ value, label }) => {
          const isBusy = busy === value
          return (
            <Button
              key={value}
              variant="outline"
              size="sm"
              onClick={() => handleDesktopSave(value)}
              disabled={isBusy}
            >
              {isBusy ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5" />
              )}
              {label}
            </Button>
          )
        })}
      </div>
    )
  }

  // Browser mode (dev / Vite): use the standard download link.
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