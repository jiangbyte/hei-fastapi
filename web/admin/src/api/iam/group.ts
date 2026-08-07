/** Author: Charlie */

import { http } from '@/utils'

const groupPrefix = '/api/v1/admin/sys/groups'

export function page(params: any) {
  return http.get<any>(`${groupPrefix}/page`, { params })
}

export function detail(params: any) {
  return http.get<any>(`${groupPrefix}/detail`, { params })
}

export function create(data: any) {
  return http.post<any>(`${groupPrefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${groupPrefix}/update`, data)
}

export function remove(data: any) {
  return http.post<any>(`${groupPrefix}/delete`, data)
}

export function ownUsers(groupId: string) {
  return http.get<any>(`${groupPrefix}/own-user`, { params: { id: groupId } })
}

export function grantUsers(data: any) {
  return http.post<any>(`${groupPrefix}/grant-user`, data)
}

export function ownRoles(groupId: string) {
  return http.get<any>(`${groupPrefix}/own-role`, { params: { id: groupId } })
}

export function grantRoles(data: any) {
  return http.post<any>(`${groupPrefix}/grant-role`, data)
}

export function ownResources(groupId: string) {
  return http.get<any>(`${groupPrefix}/own-resource`, { params: { id: groupId } })
}

export function grantResources(data: any) {
  return http.post<any>(`${groupPrefix}/grant-resource`, data)
}
