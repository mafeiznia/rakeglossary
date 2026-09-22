export type ProgressLevel = 'info' | 'success' | 'warning' | 'error'

export interface ProgressEvent {
  project_id: string
  level: ProgressLevel
  message: string
  step: string
  current: number
  total: number
  timestamp: string
  extra: Record<string, unknown>
}