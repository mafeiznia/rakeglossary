import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Ban, Check, Info, Loader2, Pencil, Trash2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tooltip } from '@/components/ui/tooltip'
import type { GlossaryEntryRead, GlossaryEntryUpdate } from '@/types'

interface Props {
  entries: GlossaryEntryRead[]
  onUpdate: (id: number, patch: GlossaryEntryUpdate) => Promise<void>
  onDelete: (id: number) => Promise<void>
  onBlacklist?: (term: string, entryId: number) => Promise<void>
}

interface EditableCellProps {
  value: string
  onSave: (v: string) => Promise<void>
  multiline?: boolean
}

function EditableCell({ value, onSave, multiline }: EditableCellProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (draft === value) {
      setEditing(false)
      return
    }
    setSaving(true)
    try {
      await onSave(draft)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    if (e.key === 'Escape') {
      setEditing(false)
      setDraft(value)
      return
    }
    if (e.key === 'Enter') {
      if (multiline && e.shiftKey) return
      e.preventDefault()
      handleSave()
    }
  }

  if (!editing) {
    const isEmpty = !value || !value.trim()
    return (
      <div
        className="group flex items-start gap-2 cursor-pointer min-h-[24px]"
        onClick={() => {
          setDraft(value)
          setEditing(true)
        }}
      >
        <span className="flex-1 whitespace-pre-wrap break-words">
          {isEmpty ? (
            <Tooltip content="ترجمه نشده — برای افزودن دستی کلیک کن">
              <span
                className="italic text-xs"
                style={{ color: 'rgb(var(--color-warning))' }}
              >
                (ترجمه نشده)
              </span>
            </Tooltip>
          ) : (
            value
          )}
        </span>
        <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-50 shrink-0 mt-1" />
      </div>
    )
  }

  return (
    <div className="flex items-start gap-1">
      {multiline ? (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 rounded border px-2 py-1 text-sm resize-y min-h-[60px]"
          style={{
            backgroundColor: 'rgb(var(--color-surface))',
            borderColor: 'rgb(var(--color-border))',
            color: 'rgb(var(--color-text))',
          }}
          autoFocus
        />
      ) : (
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          className="h-8 text-sm"
          autoFocus
        />
      )}
      <Tooltip content="ذخیره (Enter)">
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 shrink-0"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Check className="h-3 w-3" />
          )}
        </Button>
      </Tooltip>
      <Tooltip content="لغو (Esc)">
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7 shrink-0"
          onClick={() => {
            setEditing(false)
            setDraft(value)
          }}
          disabled={saving}
        >
          <X className="h-3 w-3" />
        </Button>
      </Tooltip>
    </div>
  )
}

// --- AI extras badges -------------------------------------------------------

function PosBadge({ pos }: { pos: string }) {
  if (!pos) return null
  return (
    <span
      className="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono uppercase"
      style={{
        backgroundColor: 'rgb(var(--color-surface-alt))',
        color: 'rgb(var(--color-text-muted))',
      }}
    >
      {pos}
    </span>
  )
}

function CategoryBadge({ category }: { category: string }) {
  if (!category) return null
  return (
    <span
      className="inline-block px-1.5 py-0.5 rounded text-[10px]"
      style={{
        backgroundColor: 'rgb(var(--color-primary) / 0.12)',
        color: 'rgb(var(--color-primary))',
      }}
    >
      {category}
    </span>
  )
}

function TranslatorNoteIcon({ note }: { note: string | null }) {
  if (!note || !note.trim()) return null
  return (
    <Tooltip content={note}>
      <span
        className="inline-flex items-center cursor-help"
        onClick={(e) => e.stopPropagation()}
      >
        <Info
          className="h-3.5 w-3.5"
          style={{ color: 'rgb(var(--color-info))' }}
        />
      </span>
    </Tooltip>
  )
}

function AlternativesIndicator({
  alternatives,
}: {
  alternatives: string[] | null
}) {
  if (!alternatives || alternatives.length === 0) return null
  const title = alternatives.join(' · ')
  return (
    <Tooltip content={title}>
      <span
        className="inline-block text-[10px] cursor-help"
        style={{ color: 'rgb(var(--color-text-muted))' }}
      >
        +{alternatives.length} alternative{alternatives.length > 1 ? 's' : ''}
      </span>
    </Tooltip>
  )
}

// --- Main component ---------------------------------------------------------

export function GlossaryTable({
  entries,
  onUpdate,
  onDelete,
  onBlacklist,
}: Props) {
  const { t } = useTranslation()

  if (entries.length === 0) {
    return (
      <div
        className="rounded-lg border p-10 text-center"
        style={{
          backgroundColor: 'rgb(var(--color-surface))',
          borderColor: 'rgb(var(--color-border))',
        }}
      >
        <p className="text-sm" style={{ color: 'rgb(var(--color-text-muted))' }}>
          No glossary entries
        </p>
      </div>
    )
  }

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
              <th
                className="text-center p-3 font-semibold"
                style={{ width: '3rem' }}
              >
                #
              </th>
              <th className="text-start p-3 font-semibold" dir="ltr">
                English Term
              </th>
              <th className="text-start p-3 font-semibold">Persian Term</th>
              <th className="text-start p-3 font-semibold" dir="ltr">
                <Tooltip content="جمله‌ای از متن اصلی کتاب که این واژه در آن آمده است">
                  <span className="cursor-help">Context ⓘ</span>
                </Tooltip>
              </th>
              <th className="text-start p-3 font-semibold">
                Persian Definition
              </th>
              <th
                className="text-start p-3 font-semibold"
                style={{ width: '6rem' }}
              >
                <Tooltip content={t('glossary.sourceHeader')}>
                  <span className="cursor-help">Source ⓘ</span>
                </Tooltip>
              </th>
              <th
                className="text-start p-3 font-semibold"
                style={{ width: '4rem' }}
              >
                <Tooltip content="امتیاز ترکیبی از spaCy + RAKE + YAKE (یا بر اساس frequency در حالت AI). هرچه بالاتر، مهم‌تر.">
                  <span className="cursor-help">Score ⓘ</span>
                </Tooltip>
              </th>
              <th
                className="text-start p-3 font-semibold"
                style={{ width: '4rem' }}
              >
                <Tooltip content="تعداد دفعاتی که این واژه در متن اصلی آمده است">
                  <span className="cursor-help">Freq ⓘ</span>
                </Tooltip>
              </th>
              <th style={{ width: '5rem' }}></th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, i) => (
              <tr
                key={entry.id}
                className="border-b last:border-0 hover:bg-[rgb(var(--color-surface-alt))] rg-anim-fade-in"
                style={{ borderColor: 'rgb(var(--color-border))' }}
              >
                <td
                  className="p-3 text-center font-mono text-xs align-top"
                  style={{
                    width: '3rem',
                    color: 'rgb(var(--color-text-muted))',
                  }}
                >
                  {i + 1}
                </td>

                <td className="p-3 align-top" dir="ltr">
                  <div className="flex items-center gap-1.5">
                    <EditableCell
                      value={entry.english_term}
                      onSave={(v) =>
                        onUpdate(entry.id, { english_definition: v })
                      }
                    />
                    <TranslatorNoteIcon note={entry.translator_note} />
                  </div>
                  {(entry.pos || entry.category) && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      <PosBadge pos={entry.pos || ''} />
                      <CategoryBadge category={entry.category || ''} />
                    </div>
                  )}
                </td>

                <td className="p-3 align-top" dir="rtl">
                  <EditableCell
                    value={entry.persian_term}
                    onSave={(v) => onUpdate(entry.id, { persian_term: v })}
                  />
                  {entry.persian_transliteration && (
                    <div
                      className="text-[10px] mt-1 italic"
                      dir="ltr"
                      style={{ color: 'rgb(var(--color-text-muted))' }}
                    >
                      {entry.persian_transliteration}
                    </div>
                  )}
                  {entry.persian_alternatives &&
                    entry.persian_alternatives.length > 0 && (
                      <div className="mt-1" dir="ltr">
                        <AlternativesIndicator
                          alternatives={entry.persian_alternatives}
                        />
                      </div>
                    )}
                </td>

                <td className="p-3 max-w-lg align-top" dir="ltr">
                  {entry.context && entry.context.trim() ? (
                    <span
                      className="text-sm italic whitespace-pre-wrap break-words text-start block"
                      style={{ color: 'rgb(var(--color-text-muted))' }}
                    >
                      "{entry.context}"
                    </span>
                  ) : (
                    <span
                      className="text-xs italic"
                      style={{ color: 'rgb(var(--color-text-muted))' }}
                    >
                      —
                    </span>
                  )}
                </td>

                <td className="p-3 max-w-md align-top" dir="rtl">
                  <EditableCell
                    value={entry.persian_definition}
                    onSave={(v) =>
                      onUpdate(entry.id, { persian_definition: v })
                    }
                    multiline
                  />
                </td>

                <td className="p-3 align-top" style={{ width: '6rem' }}>
                  <Tooltip
                    content={
                      t(`glossary.sourceTooltip.${entry.source}`) ||
                      entry.source
                    }
                  >
                    <span
                      className="inline-block px-2 py-0.5 rounded text-xs cursor-help"
                      style={{
                        backgroundColor: 'rgb(var(--color-surface-alt))',
                      }}
                    >
                      {entry.source}
                    </span>
                  </Tooltip>
                </td>

                <td
                  className="p-3 font-mono text-xs align-top"
                  style={{ width: '4rem' }}
                >
                  {entry.score.toFixed(3)}
                </td>

                <td
                  className="p-3 font-mono text-xs align-top"
                  style={{ width: '4rem' }}
                >
                  {entry.frequency}
                </td>

                <td className="p-3 align-top" style={{ width: '5rem' }}>
                  <div className="flex items-center gap-1 justify-end">
                    {onBlacklist && (
                      <Tooltip content={t('glossary.blacklistTooltip')}>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() =>
                            onBlacklist(entry.english_term, entry.id)
                          }
                        >
                          <Ban
                            className="h-3.5 w-3.5"
                            style={{ color: 'rgb(var(--color-warning))' }}
                          />
                        </Button>
                      </Tooltip>
                    )}
                    <Tooltip content={t('common.delete')}>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={() => onDelete(entry.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </Tooltip>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}