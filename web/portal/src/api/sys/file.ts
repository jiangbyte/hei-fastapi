import { http } from '@/utils'

const prefix = '/api/v1/portal/sys/file'

export function uploadFile(file: File) {
  const data = new FormData()
  data.append('file', file)
  return http.post<any>(`${prefix}/upload`, data)
}
