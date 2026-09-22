import type { ProjectSourceRead } from './source'

export type ProjectStatus =
  | 'pending'
  | 'processing'
  | 'done'
  | 'failed'
  | 'cancelled'

export type ProcessingMode = 'offline' | 'ai' | 'hybrid'

export interface ProjectSummary {
  id: string
  title: string
  status: ProjectStatus
  word_count: number
  source_count: number
  num_terms: number
  created_at: string
  updated_at: string
  finished_at: string | null
}

export interface ProjectRead extends ProjectSummary {
  translate_terms: boolean
  translate_definitions: boolean
  terms_per_1k_words: number
  translation_provider: string
  processing_mode: ProcessingMode
  use_spacy: boolean
  use_rake: boolean
  use_yake: boolean
  use_ner: boolean
  error_message: string | null
  started_at: string | null
  book_metadata: Record<string, unknown> | null
  sources: ProjectSourceRead[]
}

export interface ProjectListResponse {
  items: ProjectSummary[]
  total: number
  page: number
  page_size: number
}

export interface ProjectCreateEmpty {
  title: string
  num_terms?: number
  terms_per_1k_words?: number
  translate_terms?: boolean
  translate_definitions?: boolean
  translation_provider?: string
  processing_mode?: ProcessingMode
  use_spacy?: boolean
  use_rake?: boolean
  use_yake?: boolean
  use_ner?: boolean
}

export interface ProcessRequest {
  num_terms: number
  terms_per_1k_words: number
  translate_terms: boolean
  translate_definitions: boolean
  translation_provider: string
  processing_mode: ProcessingMode
  use_spacy: boolean
  use_rake: boolean
  use_yake: boolean
  use_ner: boolean
}

export interface ProjectUpdate {
  title?: string
  num_terms?: number
  terms_per_1k_words?: number
  translate_terms?: boolean
  translate_definitions?: boolean
  translation_provider?: string
  processing_mode?: ProcessingMode
  use_spacy?: boolean
  use_rake?: boolean
  use_yake?: boolean
  use_ner?: boolean
}

export type BookMetadata = Record<string, unknown>