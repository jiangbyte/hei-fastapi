/** Author: Charlie */

import { http } from '@/utils'

const dictPrefix = '/api/v1/admin/sys/dicts'

export function page(params: any) {
  return http.get<any>(`${dictPrefix}/page`, {
    params,
  })
}

export function tree(params?: any) {
  return http.get<any>(`${dictPrefix}/tree`, {
    params,
  })
}

export function detail(params: any) {
  return http.get<any>(`${dictPrefix}/detail`, {
    params,
  })
}

export function create(data: any) {
  return http.post<any>(`${dictPrefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${dictPrefix}/update`, data)
}

export function remove(data: any) {
  return http.post<any>(`${dictPrefix}/delete`, data)
}
