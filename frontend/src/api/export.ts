import type { ExportFormat } from '@/types'

export const exportApi = {
  /** Returns the download URL for the given project + format. */
  downloadUrl: (projectId: string, format: ExportFormat): string =>
    `/api/export/${projectId}/${format}`,
}