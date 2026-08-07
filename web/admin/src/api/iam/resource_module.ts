/** Author: Charlie */

import { http } from '@/utils'

const resourceModulePrefix = '/api/v1/admin/sys/resource-modules'

export function page(params: any) {
  return http.get<any>(`${resourceModulePrefix}/page`, { params })
}

export function detail(params: any) {
  return http.get<any>(`${resourceModulePrefix}/detail`, { params })
}

export function selector(params?: any) {
  return http.get<any>(`${resourceModulePrefix}/selector`, { params })
}

export function create(data: any) {
  return http.post<any>(`${resourceModulePrefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${resourceModulePrefix}/update`, data)
}

export function remove(data: any) {
  return http.post<any>(`${resourceModulePrefix}/delete`, data)
}
