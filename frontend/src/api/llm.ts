import { api } from './client'

export interface LlmConfigRead {
  enabled: boolean
  provider: string
  model: string
  base_url: string | null
  has_api_key: boolean
  api_key_masked: string | null
}

export interface LlmConfigUpdate {
  enabled?: boolean
  provider?: string
  api_key?: string
  model?: string
  base_url?: string | null
}

export interface LlmProviderInfo {
  key: string
  name: string
  default_model: string
  suggested_models: string[]
  docs_url: string
  base_url: string | null
}

export interface LlmTestResult {
  success: boolean
  message: string
  latency_ms: number | null
}

export interface LlmModelsRead {
  provider: string
  models: string[]
  user_models: string[]
  cached_models: string[]
  cached: boolean
}

export const llmApi = {
  getProviders: async (): Promise<LlmProviderInfo[]> => {
    const { data } = await api.get<LlmProviderInfo[]>(
      '/settings/llm/providers'
    )
    return data
  },

  getConfig: async (): Promise<LlmConfigRead> => {
    const { data } = await api.get<LlmConfigRead>('/settings/llm')
    return data
  },

  updateConfig: async (
    payload: LlmConfigUpdate
  ): Promise<LlmConfigRead> => {
    const { data } = await api.put<LlmConfigRead>('/settings/llm', payload)
    return data
  },

  clearConfig: async (): Promise<void> => {
    await api.delete('/settings/llm')
  },

  testConfig: async (): Promise<LlmTestResult> => {
    const { data } = await api.post<LlmTestResult>('/settings/llm/test')
    return data
  },
  getModels: async (provider: string): Promise<LlmModelsRead> => {
    const { data } = await api.get<LlmModelsRead>(
      `/settings/llm/models?provider=${encodeURIComponent(provider)}`
    )
    return data
  },

  refreshModels: async (provider: string): Promise<LlmModelsRead> => {
    const { data } = await api.post<LlmModelsRead>(
      `/settings/llm/models/refresh?provider=${encodeURIComponent(provider)}`
    )
    return data
  },

  deleteUserModel: async (
    provider: string,
    model: string
  ): Promise<void> => {
    await api.delete(
      `/settings/llm/models/user/${encodeURIComponent(provider)}/${encodeURIComponent(model)}`
    )
  },  
}