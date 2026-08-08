/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/portal/message'

export const notificationApi = {
  page: (params?: { current?: number; size?: number; category?: string }) =>
    http.get<any>(`${prefix}/notifications/my-page`, { params }),
  detail: (id: string) =>
    http.get<any>(`${prefix}/notifications/my-detail`, { params: { id } }),
  unreadCount: () => http.get<any>(`${prefix}/notifications/unread-count`),
  read: (ids: string[]) => http.post<any>(`${prefix}/notifications/read`, { ids }),
  readAll: () => http.post<any>(`${prefix}/notifications/read-all`),
}
