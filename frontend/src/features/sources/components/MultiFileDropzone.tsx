import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useTranslation } from 'react-i18next'
import { FileText, Upload } from 'lucide-react'

interface Props {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/epub+zip': ['.epub'],
  'text/plain': ['.txt'],
}

export function MultiFileDropzone({ onFiles, disabled }: Props) {
  const { t } = useTranslation()

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFiles(accepted)
    },
    [onFiles]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    multiple: true,
    disabled,
  })

  return (
    <div
      {...getRootProps()}
      className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 cursor-pointer transition-colors"
      style={{
        backgroundColor: isDragActive
          ? 'rgb(var(--color-surface-alt))'
          : 'rgb(var(--color-surface))',
        borderColor: isDragActive
          ? 'rgb(var(--color-primary))'
          : 'rgb(var(--color-border))',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <Upload
          className="h-10 w-10 mb-3"
          style={{ color: 'rgb(var(--color-primary))' }}
        />
      ) : (
        <FileText
          className="h-10 w-10 mb-3"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        />
      )}
      <p className="text-sm font-medium">{t('sources.dropzoneTitle')}</p>
      <p
        className="text-xs mt-1 text-center"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        {t('sources.dropzoneHint')}
      </p>
    </div>
  )
}