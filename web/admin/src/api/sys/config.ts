/** Author: Charlie */

import { http } from '@/utils'

const configPrefix = '/api/v1/admin/sys/config'

export function page(params: any) {
  return http.get<any>(`${configPrefix}/page`, {
    params,
  })
}

export function list(params: { category?: string }) {
  return http.get<any[]>(`${configPrefix}/list`, { params })
}

export function detail(params: any) {
  return http.get<any>(`${configPrefix}/detail`, {
    params,
  })
}

export function create(data: any) {
  return http.post<any>(`${configPrefix}/create`, data)
}

export function update(data: any) {
  return http.post<any>(`${configPrefix}/update`, data)
}

export function remove(data: any) {
  return http.post<any>(`${configPrefix}/delete`, data)
}

export function batchSave(data: {
  items: Array<{ id: string; config_key: string; config_value: string | null }>
}) {
  return http.post<any>(`${configPrefix}/batch-save`, data)
}

export function testAuditAlertWebhook(data: { webhook_url: string; webhook_secret: string }) {
  return http.post<any>(`${configPrefix}/audit-alert/test-webhook`, data, {
    skipErrorMessage: true,
  })
}
