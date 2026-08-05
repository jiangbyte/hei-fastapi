import type { AxiosInstance } from 'axios'
import { getToken } from '@/utils/storage'

declare module 'axios' {
  interface AxiosRequestConfig {
    addToken?: boolean
    skipErrorMessage?: boolean
    customErrorMessage?: string
  }
}

export function setupTokenInterceptor(http: AxiosInstance) {
  http.interceptors.request.use((config) => {
    if (config.addToken !== false) {
      const token = getToken()
      if (token) {
        config.headers.set('Authorization', token)
      }
    }
    return config
  })
}
