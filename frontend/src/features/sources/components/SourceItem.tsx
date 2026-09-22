import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileText, Loader2, Pencil, Trash2, Type, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import type { ProjectSourceRead } from '@/types'

interface Props {
  source: ProjectSourceRead
  onToggleIncluded: (included: boolean) => Promise<void>
  onRename: (name: string) => Promise<void>
  onDelete: () => Promise<void>
  isUpdating: boolean
  isRemoving: boolean
}

export function SourceItem({
  source,
  onToggleIncluded,
  onRename,
  onDelete,
  isUpdating,
  isRemoving,
}: Props) {
  const { t } = useTranslation()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(source.original_name)

  const handleSave = async () => {
    const trimmed = draft.trim()
    if (!trimmed || trimmed === source.original_name) {
      setEditing(false)
      setDraft(source.original_name)
      return
    }
    try {
      await onRename(trimmed)
      setEditing(false)
    } catch {
      // keep editing on error
    }
  }

  const Icon = source.source_type === 'file' ? FileText : Type

  return (
    <div
      className="flex items-center gap-3 rounded-lg border p-3"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
        opacity: source.included ? 1 : 0.55,
      }}
    >
      <Icon
        className="h-5 w-5 shrink-0"
        style={{
          color: source.included
            ? 'rgb(var(--color-primary))'
            : 'rgb(var(--color-text-muted))',
        }}
      />

      <div className="flex-1 min-w-0">
        {editing ? (
          <div className="flex items-center gap-2">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleSave()
                } else if (e.key === 'Escape') {
                  setEditing(false)
                  setDraft(source.original_name)
                }
              }}
              autoFocus
              className="h-8 text-sm"
            />
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 shrink-0"
              onClick={handleSave}
              disabled={isUpdating}
            >
              {isUpdating ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Check className="h-3 w-3" />
              )}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 shrink-0"
              onClick={() => {
                setEditing(false)
                setDraft(source.original_name)
              }}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2 group">
            <span className="text-sm font-medium truncate">
              {source.original_name}
            </span>
            <button
              onClick={() => setEditing(true)}
              className="opacity-0 group-hover:opacity-60 transition-opacity"
              title={t('common.edit')}
            >
              <Pencil className="h-3 w-3" />
            </button>
          </div>
        )}
        <div
          className="text-xs mt-0.5 flex items-center gap-2"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          <span className="uppercase">{source.source_type}</span>
          <span>·</span>
          <span>{source.word_count.toLocaleString()} words</span>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <div title={source.included ? t('sources.excluded') : t('sources.included')}>
          <Switch
            checked={source.included}
            onCheckedChange={onToggleIncluded}
            disabled={isUpdating}
          />
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={() => {
            if (confirm(`Delete source "${source.original_name}"?`)) {
              onDelete()
            }
          }}
          disabled={isRemoving}
          title={t('common.delete')}
        >
          {isRemoving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2
              className="h-3.5 w-3.5"
              style={{ color: 'rgb(var(--color-error))' }}
            />
          )}
        </Button>
      </div>
    </div>
  )
}