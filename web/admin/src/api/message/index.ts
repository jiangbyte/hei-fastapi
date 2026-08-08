/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/admin/message'

// ── 通知（当前用户）──────────────────────────────────────────

export function notificationMyPage(params?: {
  current?: number
  size?: number
  category?: string
}) {
  return http.get<any>(`${prefix}/notifications/my-page`, { params })
}

export function notificationMyDetail(id: string) {
  return http.get<any>(`${prefix}/notifications/my-detail`, { params: { id } })
}

export function notificationUnreadCount() {
  return http.get<any>(`${prefix}/notifications/unread-count`)
}

export function readNotification(data: { ids: string[] }) {
  return http.post<any>(`${prefix}/notifications/read`, data)
}

export function readAllNotification() {
  return http.post<any>(`${prefix}/notifications/read-all`)
}

// ── 公告（当前用户）──────────────────────────────────────────

export function announcementMyPage(params?: { current?: number; size?: number }) {
  return http.get<any>(`${prefix}/announcements/my-page`, { params })
}

export function announcementMyDetail(id: string) {
  return http.get<any>(`${prefix}/announcements/my-detail`, { params: { id } })
}

export function announcementUnreadCount() {
  return http.get<any>(`${prefix}/announcements/unread-count`)
}

export function readAnnouncement(data: { ids: string[] }) {
  return http.post<any>(`${prefix}/announcements/read`, data)
}

export function readAllAnnouncement() {
  return http.post<any>(`${prefix}/announcements/read-all`)
}
