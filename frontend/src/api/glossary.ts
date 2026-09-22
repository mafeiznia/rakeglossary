import { api } from './client'
import type {
  GlossaryEntryRead,
  GlossaryEntryUpdate,
  GlossaryResponse,
} from '@/types'

export const glossaryApi = {
  list: async (projectId: string): Promise<GlossaryResponse> => {
    const { data } = await api.get<GlossaryResponse>(
      `/projects/${projectId}/glossary`
    )
    return data
  },

  update: async (
    entryId: number,
    payload: GlossaryEntryUpdate
  ): Promise<GlossaryEntryRead> => {
    const { data } = await api.patch<GlossaryEntryRead>(
      `/glossary/${entryId}`,
      payload
    )
    return data
  },

  delete: async (entryId: number): Promise<void> => {
    await api.delete(`/glossary/${entryId}`)
  },
}