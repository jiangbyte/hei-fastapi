/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/admin/sys/storage-config'

export function list() {
  return http.get<any[]>(`${prefix}/list`)
}

export function create(data: any) {
  return http.post<any>(`${prefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${prefix}/update`, data)
}

export function remove(data: { ids: string[] }) {
  return http.post<any>(`${prefix}/delete`, data)
}

export function setDefault(data: { id: string }) {
  return http.post<any>(`${prefix}/set-default`, data)
}
