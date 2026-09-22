import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useTranslation } from 'react-i18next'
import { FileText, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  file: File | null
  onFile: (file: File | null) => void
}

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/epub+zip': ['.epub'],
  'text/plain': ['.txt'],
}

export function FileDropzone({ file, onFile }: Props) {
  const { t } = useTranslation()

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFile(accepted[0])
    },
    [onFile]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    multiple: false,
  })

  if (file) {
    return (
      <div
        className="flex items-center justify-between rounded-lg border p-4"
        style={{
          backgroundColor: 'rgb(var(--color-surface-alt))',
          borderColor: 'rgb(var(--color-border))',
        }}
      >
        <div className="flex items-center gap-3 min-w-0">
          <FileText
            className="h-5 w-5 shrink-0"
            style={{ color: 'rgb(var(--color-primary))' }}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p
              className="text-xs"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => onFile(null)}
          title={t('common.remove')}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors"
      style={{
        backgroundColor: isDragActive
          ? 'rgb(var(--color-surface-alt))'
          : 'rgb(var(--color-surface))',
        borderColor: isDragActive
          ? 'rgb(var(--color-primary))'
          : 'rgb(var(--color-border))',
      }}
    >
      <input {...getInputProps()} />
      <FileText
        className="h-10 w-10 mb-3"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      />
      <p className="text-sm font-medium">{t('home.fileDropzone')}</p>
      <p
        className="text-xs mt-1 text-center"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        {t('home.fileDropzoneHint')}
      </p>
    </div>
  )
}