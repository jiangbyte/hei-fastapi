import type { AxiosError, AxiosResponse } from 'axios'
import { message } from 'antd'
import type { ApiResponse } from '@/typing/api'

const loginPath = '/auth/login'
let isHandlingUnauthorized = false

const httpStatusMessageMap: Record<number, string> = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '无权访问',
  404: '资源不存在',
  422: '校验失败',
  500: '服务器错误',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时',
}

export class ApiResponseError<T = unknown> extends Error {
  readonly apiCode: number
  readonly apiData: T
  readonly rawData: ApiResponse<T>

  constructor(response: ApiResponse<T>) {
    super(response.message || `请求失败，错误码 ${response.code}`)
    this.name = 'ApiResponseError'
    this.apiCode = response.code
    this.apiData = response.data
    this.rawData = response
  }
}

export function unwrapResponseData(response: AxiosResponse) {
  if (isApiResponse(response.data)) {
    if (response.data.code !== 200) {
      throw new ApiResponseError(response.data)
    }
    return response.data.data
  }
  return response.data
}

export function handleHttpError(error: AxiosError) {
  if (isUnauthorizedError(error) && error.config?.addToken !== false) {
    handleUnauthorizedError(error)
    return Promise.reject(error)
  }

  showErrorMessage(error)
  return Promise.reject(error)
}

function isApiResponse(data: unknown): data is ApiResponse {
  return isRecord(data) && typeof data.code === 'number'
}

function isRecord(data: unknown): data is Record<string, unknown> {
  return typeof data === 'object' && data !== null
}

function isUnauthorizedError(error: AxiosError) {
  return error.response?.status === 401 || getApiCode(error) === 401
}

function getApiCode(error: AxiosError) {
  const apiCode = (error as { apiCode?: number }).apiCode
  if (typeof apiCode === 'number') {
    return apiCode
  }

  const responseData = error.response?.data
  if (isRecord(responseData) && typeof responseData.code === 'number') {
    return responseData.code
  }

  const rawData = error.response?.rawData
  if (isRecord(rawData) && typeof rawData.code === 'number') {
    return rawData.code
  }

  return undefined
}

function handleUnauthorizedError(error: AxiosError) {
  if (isHandlingUnauthorized) {
    return
  }

  isHandlingUnauthorized = true
  const msg = getErrorMessage(error)
  if (msg) {
    message.error(msg)
  }

  void redirectToLogin().finally(() => {
    window.setTimeout(() => {
      isHandlingUnauthorized = false
    }, 1000)
  })
}

async function redirectToLogin() {
  const { useAuthStore } = await import('@/stores/auth')
  useAuthStore.getState().resetSession()

  const { pathname, search } = window.location
  if (pathname.startsWith('/auth')) {
    if (pathname !== loginPath) {
      window.location.replace(loginPath)
    }
    return
  }

  const redirect = `${pathname}${search}`
  const query = redirect && redirect !== '/' ? `?redirect=${encodeURIComponent(redirect)}` : ''
  window.location.replace(`${loginPath}${query}`)
}

function showErrorMessage(error: AxiosError) {
  if (error.config?.skipErrorMessage) {
    return
  }

  const msg = getErrorMessage(error)
  if (msg) {
    message.error(msg)
  }
}

function getErrorMessage(error: AxiosError) {
  const customErrorMessage = error.config?.customErrorMessage
  if (customErrorMessage) {
    return customErrorMessage
  }

  const responseMessage = getResponseMessage(error.response?.data)
  if (responseMessage) {
    return responseMessage
  }

  const status = error.response?.status
  if (status) {
    return httpStatusMessageMap[status] ?? `请求失败(${status})`
  }

  return '网络异常，请稍后重试'
}

function getResponseMessage(data: unknown) {
  if (isRecord(data) && typeof data.message === 'string') {
    return data.message
  }
  return undefined
}
