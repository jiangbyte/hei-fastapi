export interface ApiResponse<T = unknown> {
  code: number
  message?: string
  data: T
}

export interface PageData<T> {
  current: number
  size: number
  total: number
  pages?: number
  records: T[]
}
