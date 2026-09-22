import { api } from './client'

export interface StopwordsResponse {
  words: string[]
  total: number
}

export const settingsApi = {
  getStopwords: async (): Promise<StopwordsResponse> => {
    const { data } = await api.get<StopwordsResponse>('/settings/stopwords')
    return data
  },

  addStopword: async (word: string): Promise<StopwordsResponse> => {
    const { data } = await api.post<StopwordsResponse>(
      '/settings/stopwords',
      { word }
    )
    return data
  },

  removeStopword: async (word: string): Promise<StopwordsResponse> => {
    const { data } = await api.delete<StopwordsResponse>(
      `/settings/stopwords/${encodeURIComponent(word)}`
    )
    return data
  },
}