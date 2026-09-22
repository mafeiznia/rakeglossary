export type SourceType = 'file' | 'text'

export interface ProjectSourceRead {
  id: number
  project_id: string
  source_type: SourceType
  original_name: string
  path: string | null
  word_count: number
  order_index: number
  included: boolean
  created_at: string
  updated_at: string
}

export interface TextSourceCreate {
  name: string
  text: string
}

export interface ProjectSourceUpdate {
  original_name?: string
  included?: boolean
}