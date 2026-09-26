import { api } from './client'
import type { ExportFormat } from '@/types'

export interface SaveExportResponse {
  path: string
  filename: string
  size_bytes: number
  folder_opened: boolean
}

export const exportApi = {
  /** Returns the download URL for the given project + format. */
  downloadUrl: (projectId: string, format: ExportFormat): string =>
    `/api/export/${projectId}/${format}`,

  /**
   * Save the export to the user's Downloads folder and reveal it
   * in the OS file manager. Used in the desktop (pywebview) build
   * where browser downloads are not available.
   */
  saveToDownloads: async (
    projectId: string,
    format: ExportFormat
  ): Promise<SaveExportResponse> => {
    const { data } = await api.post<SaveExportResponse>(
      `/export/${projectId}/${format}/save`
    )
    return data
  },
}