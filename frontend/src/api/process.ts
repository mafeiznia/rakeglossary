import { api } from './client'
import type { ProcessRequest, ProjectRead } from '@/types'

export const processApi = {
  start: async (projectId: string, payload: ProcessRequest): Promise<ProjectRead> => {
    const { data } = await api.post<ProjectRead>(`/process/${projectId}`, payload)
    return data
  },

  cancel: async (projectId: string): Promise<ProjectRead> => {
    const { data } = await api.post<ProjectRead>(`/process/${projectId}/cancel`)
    return data
  },

  eventsUrl: (projectId: string): string => `/api/process/${projectId}/events`,
}