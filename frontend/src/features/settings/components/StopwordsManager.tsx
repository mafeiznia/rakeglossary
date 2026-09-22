import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Ban, Loader2, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/ui/empty-state'
import { useStopwords } from '../hooks/useStopwords'

/** Return true if the text contains at least one Persian/Arabic character. */
function containsPersian(text: string): boolean {
  for (const c of text) {
    const code = c.charCodeAt(0)
    if (
      (code >= 0x0600 && code <= 0x06ff) ||
      (code >= 0xfb50 && code <= 0xfdff)
    ) {
      return true
    }
  }
  return false
}

export function StopwordsManager() {
  const { t } = useTranslation()
  const {
    words,
    total,
    isLoading,
    add,
    remove,
    isAdding,
    isRemoving,
  } = useStopwords()
  const [draft, setDraft] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleChange = (value: string) => {
    if (containsPersian(value)) {
      // Reject the new value; keep previous draft intact
      setError(t('settings.blacklistEnglishOnly'))
      return
    }
    setError(null)
    setDraft(value)
  }

  const handleAdd = async () => {
    const w = draft.trim()
    if (!w) return
    if (containsPersian(w)) {
      setError(t('settings.blacklistEnglishOnly'))
      return
    }
    try {
      await add(w)
      setDraft('')
      setError(null)
    } catch {
      // error handled by React Query; ignore for now
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <section className="space-y-3">
      <div>
        <h3 className="text-lg font-semibold">{t('settings.blacklist')}</h3>
        <p
          className="text-xs mt-1"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          {t('settings.blacklistHint')}
        </p>
      </div>

      {/* Add new word */}
      <div className="space-y-2 max-w-md">
        <div className="flex gap-2">
          <Input
            value={draft}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('settings.blacklistPlaceholder')}
            disabled={isAdding}
            maxLength={100}
            aria-invalid={!!error}
          />
          <Button
            onClick={handleAdd}
            disabled={!draft.trim() || isAdding || !!error}
            size="default"
          >
            {isAdding ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            {t('settings.blacklistAdd')}
          </Button>
        </div>

        {error && (
          <div
            className="flex items-start gap-2 rounded-md border p-2 text-xs"
            style={{
              borderColor: 'rgb(var(--color-error))',
              color: 'rgb(var(--color-error))',
            }}
          >
            <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* List */}
      {isLoading ? (
        <div
          className="flex items-center gap-2 text-sm"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          <Loader2 className="h-4 w-4 animate-spin" />
          {t('common.loading')}
        </div>
      ) : total === 0 ? (
        <EmptyState
          icon={Ban}
          title={t('settings.blacklistEmptyTitle')}
          description={t('settings.blacklistEmpty')}
          size="compact"
        />
      ) : (
        <div className="flex flex-wrap gap-2">
          {words.map((word) => (
            <span
              key={word}
              className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-sm"
              style={{
                backgroundColor: 'rgb(var(--color-surface))',
                borderColor: 'rgb(var(--color-border))',
              }}
            >
              <span>{word}</span>
              <button
                onClick={() => remove(word)}
                disabled={isRemoving}
                className="rounded hover:opacity-70 transition-opacity"
                title={t('common.delete')}
              >
                <Trash2
                  className="h-3 w-3"
                  style={{ color: 'rgb(var(--color-error))' }}
                />
              </button>
            </span>
          ))}
        </div>
      )}

      {total > 0 && (
        <p
          className="text-xs"
          style={{ color: 'rgb(var(--color-text-muted))' }}
        >
          {t('settings.blacklistCount', { count: total })}
        </p>
      )}
    </section>
  )
}