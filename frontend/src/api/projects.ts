import { api } from './client'
import type {
  ProjectCreateEmpty,
  ProjectListResponse,
  ProjectRead,
  ProjectUpdate,
} from '@/types'

export const projectsApi = {
  list: async (page = 1, pageSize = 50): Promise<ProjectListResponse> => {
    const { data } = await api.get<ProjectListResponse>('/projects', {
      params: { page, page_size: pageSize },
    })
    return data
  },

  get: async (id: string): Promise<ProjectRead> => {
    const { data } = await api.get<ProjectRead>(`/projects/${id}`)
    return data
  },

  createEmpty: async (payload: ProjectCreateEmpty): Promise<ProjectRead> => {
    const { data } = await api.post<ProjectRead>('/projects', payload)
    return data
  },

  update: async (id: string, payload: ProjectUpdate): Promise<ProjectRead> => {
    const { data } = await api.patch<ProjectRead>(`/projects/${id}`, payload)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`)
  },
  
    updateMetadata: async (
    id: string,
    metadata: Record<string, unknown>
  ): Promise<ProjectRead> => {
    const { data } = await api.put<ProjectRead>(
      `/projects/${id}/metadata`,
      metadata
    )
    return data
  },

  clearMetadata: async (id: string): Promise<ProjectRead> => {
    const { data } = await api.delete<ProjectRead>(
      `/projects/${id}/metadata`
    )
    return data
  },
}