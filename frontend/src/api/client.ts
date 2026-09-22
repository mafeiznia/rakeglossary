import axios, { AxiosError } from 'axios'

export interface ApiError {
  detail: string | Array<{ msg?: string; loc?: unknown[] }> | Record<string, unknown>
  code?: string
}

function stringifyDetail(detail: unknown): string {
  if (detail == null) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        if (typeof e === 'string') return e
        if (e && typeof e === 'object' && 'msg' in e) {
          const msg = (e as { msg: unknown }).msg
          const loc = (e as { loc?: unknown[] }).loc
          const locStr = Array.isArray(loc) ? loc.join('.') : ''
          return locStr ? `${locStr}: ${String(msg)}` : String(msg)
        }
        try {
          return JSON.stringify(e)
        } catch {
          return String(e)
        }
      })
      .join('; ')
  }
  if (typeof detail === 'object') {
    const obj = detail as Record<string, unknown>
    if (typeof obj.message === 'string') return obj.message
    try {
      return JSON.stringify(detail)
    } catch {
      return 'Unknown error'
    }
  }
  return String(detail)
}

export const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const detail = error.response?.data?.detail
    const message =
      stringifyDetail(detail) || error.message || 'Unknown API error'
    return Promise.reject(new Error(message))
  }
)