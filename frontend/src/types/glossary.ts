export interface GlossaryEntryRead {
  id: number
  project_id: string
  english_term: string
  persian_term: string
  english_definition: string
  persian_definition: string
  source: string
  score: number
  frequency: number
  context: string
  is_edited: boolean
  // --- AI Mode extras (nullable) ---
  pos: string | null
  category: string | null
  persian_alternatives: string[] | null
  translator_note: string | null
  persian_transliteration: string | null
  // --- Timestamps ---
  created_at: string
  updated_at: string
}

export interface GlossaryEntryUpdate {
  persian_term?: string
  persian_definition?: string
  english_definition?: string
  translator_note?: string
  is_edited?: boolean
}

export interface GlossaryResponse {
  project_id: string
  entries: GlossaryEntryRead[]
  total: number
}

export type ExportFormat = 'csv' | 'xlsx' | 'tbx'