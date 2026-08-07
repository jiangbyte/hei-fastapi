/** Author: Charlie */

import { http } from '@/utils'

const prefix = '/api/v1/admin/message'

// ── 会话 ─────────────────────────────────────────────────────

export function conversationList(params?: { current?: number; size?: number }) {
  return http.get<any>(`${prefix}/conversations/my-list`, { params })
}

export function conversationDetail(id: string) {
  return http.get<any>(`${prefix}/conversations/detail`, { params: { id } })
}

export function createDirectConversation(data: { account_type: string; account_id: string }) {
  return http.post<any>(`${prefix}/conversations/create-direct`, data)
}

export function muteConversation(data: { conversation_id: string; is_muted: boolean }) {
  return http.post<any>(`${prefix}/conversations/mute`, data)
}

export function pinConversation(data: { conversation_id: string; is_pinned: boolean }) {
  return http.post<any>(`${prefix}/conversations/pin`, data)
}

export function leaveConversation(data: { id: string }) {
  return http.post<any>(`${prefix}/conversations/leave`, data)
}

export function markConversationRead(data: { id: string }) {
  return http.post<any>(`${prefix}/conversations/mark-read`, data)
}

// ── 消息 ──────────────────────────────────────────────────────────

export function sendMessage(data: {
  conversation_id?: string
  group_id?: string
  participant_refs?: Array<{ account_type: string; account_id: string }>
  client_msg_id: string
  title?: string
  parent_id?: string
  content: string
  content_type?: string
  msg_type?: string
  sender_name?: string
  attachments?: Array<{
    file_id?: string
    name: string
    url: string
    content_type?: string
    size?: number
    attachment_type?: string
    thumbnail_url?: string
    sort?: number
    extra?: Record<string, any>
  }>
  extra?: Record<string, any>
}) {
  return http.post<any>(`${prefix}/messages/send`, data)
}

export function replyMessage(data: {
  conversation_id?: string
  parent_id: string
  content: string
  content_type?: string
  msg_type?: string
  attachments?: Array<any>
  extra?: Record<string, any>
}) {
  return http.post<any>(`${prefix}/messages/reply`, data)
}

export function revokeMessage(data: { message_id: string }) {
  return http.post<any>(`${prefix}/messages/revoke`, data)
}

export function readMessage(data: { conversation_id: string; terminal_id?: string }) {
  return http.post<any>(`${prefix}/messages/read`, data)
}

export function messagePage(params: { conversation_id: string; current?: number; size?: number }) {
  return http.get<any>(`${prefix}/messages/page`, { params })
}

export function unreadCount(conversationId: string) {
  return http.get<any>(`${prefix}/messages/unread-count`, {
    params: { conversation_id: conversationId },
  })
}

// ── 群组 ────────────────────────────────────────────────────────────

export function groupList() {
  return http.get<any[]>(`${prefix}/groups/my-list`)
}

export function groupDetail(id: string) {
  return http.get<any>(`${prefix}/groups/detail`, { params: { id } })
}

export function createGroup(data: {
  name: string
  avatar?: string
  description?: string
  join_mode?: string
  max_members?: number
}) {
  return http.post<any>(`${prefix}/groups/create`, data)
}

export function updateGroup(data: {
  id: string
  name?: string
  avatar?: string
  description?: string
  join_mode?: string
  max_members?: number
}) {
  return http.post<any>(`${prefix}/groups/update`, data)
}

export function dissolveGroup(data: { id: string }) {
  return http.post<any>(`${prefix}/groups/dissolve`, data)
}

export function leaveGroup(data: { id: string }) {
  return http.post<any>(`${prefix}/groups/leave`, data)
}

export function groupMemberList(id: string) {
  return http.get<any[]>(`${prefix}/groups/members/list`, { params: { id } })
}

export function searchGroups(keyword: string) {
  return http.get<any[]>(`${prefix}/groups/search`, { params: { keyword } })
}

export function addGroupMembers(data: {
  group_id: string
  members: Array<{ account_type: string; account_id: string }>
}) {
  return http.post<any>(`${prefix}/groups/members/add`, data)
}

export function removeGroupMember(data: {
  group_id: string
  account_type: string
  account_id: string
}) {
  return http.post<any>(`${prefix}/groups/members/remove`, data)
}

export function setGroupMemberRole(data: {
  group_id: string
  account_type: string
  account_id: string
  role: string
}) {
  return http.post<any>(`${prefix}/groups/members/set-role`, data)
}

export function applyJoinGroup(data: { group_id: string; message?: string }) {
  return http.post<any>(`${prefix}/groups/join-requests/apply`, data)
}

export function handleJoinGroupRequest(data: { id: string; status: string }) {
  return http.post<any>(`${prefix}/groups/join-requests/handle`, data)
}

export function myJoinRequests() {
  return http.get<any[]>(`${prefix}/groups/join-requests/my`)
}

export function pendingJoinRequests() {
  return http.get<any[]>(`${prefix}/groups/join-requests/pending`)
}

export function pendingJoinRequestCount() {
  return http.get<any>(`${prefix}/groups/join-requests/pending-count`)
}

// ── 好友 ───────────────────────────────────────────────────────────

export function friendList() {
  return http.get<any[]>(`${prefix}/friends/my-list`)
}

export function searchUsers(keyword: string) {
  return http.get<any[]>(`${prefix}/friends/search`, { params: { keyword } })
}

export function applyFriend(data: {
  applicant_type: string
  applicant_id: string
  recipient_type: string
  recipient_id: string
  message?: string
}) {
  return http.post<any>(`${prefix}/friends/apply`, data)
}

export function handleFriendRequest(data: { request_id: string; action: string }) {
  return http.post<any>(`${prefix}/friends/handle-request`, data)
}

export function removeFriend(data: { friendship_id: string }) {
  return http.post<any>(`${prefix}/friends/remove`, data)
}

export function setFriendRemark(data: { friendship_id: string; remark?: string }) {
  return http.post<any>(`${prefix}/friends/set-remark`, data)
}

export function myFriendRequests() {
  return http.get<any[]>(`${prefix}/friends/my-requests`)
}

export function myFriendRequestCount() {
  return http.get<any>(`${prefix}/friends/my-request-count`)
}

// ── 通知 ────────────────────────────────────────────────────

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

// ── 公告 ────────────────────────────────────────────────────

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

/** IM AUTH 用的一次性短期 ticket（优先于长期 session token）。 */
export function imTicket() {
  return http.post<{ ticket: string; expires_in: number }>(`${prefix}/im/ticket`)
}
