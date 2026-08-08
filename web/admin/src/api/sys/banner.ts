/** Author: Charlie */

import { API_PREFIX } from '@/constants/api'
import { http } from '@/utils'

const bannerPrefix = `${API_PREFIX}/sys/banners`

export function page(params: any) {
  return http.get<any>(`${bannerPrefix}/page`, { params })
}
export function detail(params: any) {
  return http.get<any>(`${bannerPrefix}/detail`, { params })
}
export function create(data: any) {
  return http.post<any>(`${bannerPrefix}/create`, data)
}
export function update(data: any) {
  return http.post<any>(`${bannerPrefix}/update`, data)
}
export function remove(data: any) {
  return http.post<any>(`${bannerPrefix}/delete`, data)
}
