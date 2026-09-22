import { api } from './client'
import type {
  ProjectSourceRead,
  ProjectSourceUpdate,
  TextSourceCreate,
} from '@/types'

export const sourcesApi = {
  list: async (projectId: string): Promise<ProjectSourceRead[]> => {
    const { data } = await api.get<ProjectSourceRead[]>(
      `/projects/${projectId}/sources`
    )
    return data
  },

  uploadFiles: async (
    projectId: string,
    files: File[]
  ): Promise<ProjectSourceRead[]> => {
    const form = new FormData()
    for (const f of files) {
      form.append('files', f, f.name)
    }
    const { data } = await api.post<ProjectSourceRead[]>(
      `/projects/${projectId}/sources/upload`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data
  },

  addText: async (
    projectId: string,
    payload: TextSourceCreate
  ): Promise<ProjectSourceRead> => {
    const { data } = await api.post<ProjectSourceRead>(
      `/projects/${projectId}/sources/text`,
      payload
    )
    return data
  },

  update: async (
    projectId: string,
    sourceId: number,
    payload: ProjectSourceUpdate
  ): Promise<ProjectSourceRead> => {
    const { data } = await api.patch<ProjectSourceRead>(
      `/projects/${projectId}/sources/${sourceId}`,
      payload
    )
    return data
  },

  remove: async (projectId: string, sourceId: number): Promise<void> => {
    await api.delete(`/projects/${projectId}/sources/${sourceId}`)
  },
}