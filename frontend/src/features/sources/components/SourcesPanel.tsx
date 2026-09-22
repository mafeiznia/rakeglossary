import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileText, Loader2, Plus, Type } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useSources } from '../hooks/useSources'
import { MultiFileDropzone } from './MultiFileDropzone'
import { SourceItem } from './SourceItem'
import { useConfirm } from '@/features/confirm/confirmStore'
import { FolderOpen } from 'lucide-react'
import { EmptyState } from '@/components/ui/empty-state'

interface Props {
  projectId: string
}

export function SourcesPanel({ projectId }: Props) {
  const { t } = useTranslation()
  const confirm = useConfirm()
  const {
    sources,
    isLoading,
    upload,
    addText,
    update,
    remove,
    isUploading,
    isAddingText,
    isUpdating,
    isRemoving,
  } = useSources(projectId)

  const [showAdd, setShowAdd] = useState(false)
  const [tab, setTab] = useState<'file' | 'text'>('file')
  const [textName, setTextName] = useState('')
  const [textBody, setTextBody] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (files: File[]) => {
    setError(null)
    try {
      await upload(files)
      setShowAdd(false)
      toast.success(t('toast.saved'))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleAddText = async () => {
    setError(null)
    if (!textName.trim() || !textBody.trim()) {
      setError(t('sources.errorEmptyText'))
      return
    }
    try {
      await addText({ name: textName.trim(), text: textBody })
      setTextName('')
      setTextBody('')
      setShowAdd(false)
      toast.success(t('toast.saved'))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleDelete = async (sourceId: number, sourceName: string) => {
    const ok = await confirm({
      title: t('confirm.deleteSource.title'),
      description: t('confirm.deleteSource.description', { name: sourceName }),
      confirmLabel: t('common.delete'),
      variant: 'destructive',
    })
    if (!ok) return
    try {
      await remove(sourceId)
      toast.success(t('toast.sourceDeleted'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const includedCount = sources.filter((s) => s.included).length

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{t('sources.title')}</h3>
          <p
            className="text-xs mt-0.5"
            style={{ color: 'rgb(var(--color-text-muted))' }}
          >
            {isLoading
              ? t('common.loading')
              : `${sources.length} ${t('sources.totalLabel')} · ${includedCount} ${t('sources.activeLabel')}`}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAdd((v) => !v)}
          disabled={isUploading || isAddingText}
        >
          <Plus className="h-3.5 w-3.5" />
          {t('sources.addButton')}
        </Button>
      </div>

      {showAdd && (
        <div
          className="rounded-lg border p-4 space-y-3"
          style={{
            backgroundColor: 'rgb(var(--color-surface))',
            borderColor: 'rgb(var(--color-border))',
          }}
        >
          <Tabs value={tab} onValueChange={(v) => setTab(v as 'file' | 'text')}>
            <TabsList>
              <TabsTrigger value="file">
                <FileText className="h-3.5 w-3.5 me-1" />
                {t('sources.tabFile')}
              </TabsTrigger>
              <TabsTrigger value="text">
                <Type className="h-3.5 w-3.5 me-1" />
                {t('sources.tabText')}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="file">
              <MultiFileDropzone onFiles={handleUpload} disabled={isUploading} />
              {isUploading && (
                <div className="flex items-center gap-2 mt-2 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t('sources.uploading')}
                </div>
              )}
            </TabsContent>

            <TabsContent value="text">
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="source-text-name">
                    {t('sources.textName')}
                  </Label>
                  <Input
                    id="source-text-name"
                    value={textName}
                    onChange={(e) => setTextName(e.target.value)}
                    placeholder={t('sources.textNamePlaceholder')}
                    maxLength={255}
                    disabled={isAddingText}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="source-text-body">
                    {t('sources.textBody')}
                  </Label>
                  <Textarea
                    id="source-text-body"
                    value={textBody}
                    onChange={(e) => setTextBody(e.target.value)}
                    placeholder={t('sources.textBodyPlaceholder')}
                    rows={8}
                    disabled={isAddingText}
                  />
                  <p
                    className="text-xs"
                    style={{ color: 'rgb(var(--color-text-muted))' }}
                  >
                    {t('sources.textStats', {
                      words: textBody.trim()
                        ? textBody.trim().split(/\s+/).length
                        : 0,
                      chars: textBody.length,
                    })}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleAddText}
                    disabled={
                      isAddingText ||
                      !textName.trim() ||
                      !textBody.trim()
                    }
                    size="sm"
                  >
                    {isAddingText ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Plus className="h-3.5 w-3.5" />
                    )}
                    {t('sources.textAdd')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAdd(false)}
                    disabled={isAddingText}
                  >
                    {t('common.cancel')}
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {error && (
            <div
              className="rounded-md border p-2 text-xs"
              style={{
                borderColor: 'rgb(var(--color-error))',
                color: 'rgb(var(--color-error))',
              }}
            >
              {error}
            </div>
          )}
        </div>
      )}

      {sources.length === 0 && !isLoading ? (
        <EmptyState
          icon={FolderOpen}
          title={t('sources.emptyTitle')}
          description={t('sources.empty')}
          actionLabel={t('sources.addButton')}
          onAction={() => setShowAdd(true)}
          size="compact"
        />
      ) : (
        <div className="space-y-2">
          {sources.map((src) => (
            <SourceItem
              key={src.id}
              source={src}
              onToggleIncluded={async (included) => {
                await update({ sourceId: src.id, payload: { included } })
              }}
              onRename={async (original_name) => {
                await update({ sourceId: src.id, payload: { original_name } })
              }}
              onDelete={async () => {
                await handleDelete(src.id, src.original_name)
              }}
              isUpdating={isUpdating}
              isRemoving={isRemoving}
            />
          ))}
        </div>
      )}
    </div>
  )
}