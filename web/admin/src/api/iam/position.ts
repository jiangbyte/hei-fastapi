/** Author: Charlie */

import { http } from '@/utils'

const positionPrefix = '/api/v1/admin/sys/positions'

export function page(params: any) {
  return http.get<any>(`${positionPrefix}/page`, { params })
}

export function detail(params: any) {
  return http.get<any>(`${positionPrefix}/detail`, { params })
}

export function create(data: any) {
  return http.post<any>(`${positionPrefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${positionPrefix}/update`, data)
}

export function remove(data: any) {
  return http.post<any>(`${positionPrefix}/delete`, data)
}
