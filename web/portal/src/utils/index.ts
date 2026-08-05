import { createHttp } from './axios'

export * from './dict'
export * from './storage'
export * from './time'
export * from './validate'
export { encryptPasswords } from './security'
export { ApiResponseError, createHttp } from './axios'

export const http = createHttp({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 15000,
})
