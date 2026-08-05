import { http } from '@/utils'

const prefix = '/api/v1/portal/message'

export const imApi = {
  conversationList: (params?: any) =>
    http.get<any>(`${prefix}/conversations/my-list`, { params }),
  conversationDetail: (id: string) =>
    http.get<any>(`${prefix}/conversations/detail`, { params: { id } }),
  createDirect: (data: any) =>
    http.post<any>(`${prefix}/conversations/create-direct`, data),
  markConversationRead: (data: any) =>
    http.post<any>(`${prefix}/conversations/mark-read`, data),
  leaveConversation: (data: any) =>
    http.post<any>(`${prefix}/conversations/leave`, data),

  sendMessage: (data: any) => http.post<any>(`${prefix}/messages/send`, data),
  messagePage: (params: any) =>
    http.get<any>(`${prefix}/messages/page`, { params }),
  unreadCount: (conversationId: string) =>
    http.get<any>(`${prefix}/messages/unread-count`, {
      params: { conversation_id: conversationId },
    }),
  revokeMessage: (data: any) =>
    http.post<any>(`${prefix}/messages/revoke`, data),

  friendList: () => http.get<any>(`${prefix}/friends/my-list`),
  searchUsers: (keyword: string) =>
    http.get<any>(`${prefix}/friends/search`, { params: { keyword } }),
  applyFriend: (data: any) => http.post<any>(`${prefix}/friends/apply`, data),
  handleFriendRequest: (data: any) =>
    http.post<any>(`${prefix}/friends/handle-request`, data),
  removeFriend: (data: any) =>
    http.post<any>(`${prefix}/friends/remove`, data),
  myFriendRequests: () => http.get<any>(`${prefix}/friends/my-requests`),
  myFriendRequestCount: () =>
    http.get<any>(`${prefix}/friends/my-request-count`),

  groupList: () => http.get<any>(`${prefix}/groups/my-list`),
  searchGroups: (keyword: string) =>
    http.get<any>(`${prefix}/groups/search`, { params: { keyword } }),
  createGroup: (data: any) =>
    http.post<any>(`${prefix}/groups/create`, data),
  dissolveGroup: (data: any) => http.post<any>(`${prefix}/groups/dissolve`, data),
  leaveGroup: (data: any) => http.post<any>(`${prefix}/groups/leave`, data),
  groupMemberList: (id: string) =>
    http.get<any>(`${prefix}/groups/members/list`, { params: { id } }),
  addGroupMembers: (data: any) =>
    http.post<any>(`${prefix}/groups/members/add`, data),
  removeGroupMember: (data: any) =>
    http.post<any>(`${prefix}/groups/members/remove`, data),
  setGroupMemberRole: (data: any) =>
    http.post<any>(`${prefix}/groups/members/set-role`, data),
  applyJoinGroup: (data: any) =>
    http.post<any>(`${prefix}/groups/join-requests/apply`, data),
  handleJoinGroupRequest: (data: any) =>
    http.post<any>(`${prefix}/groups/join-requests/handle`, data),
  myJoinRequests: () => http.get<any>(`${prefix}/groups/join-requests/my`),
  pendingJoinRequests: () => http.get<any>(`${prefix}/groups/join-requests/pending`),
  pendingJoinRequestCount: () => http.get<any>(`${prefix}/groups/join-requests/pending-count`),

  notificationPage: (params?: any) =>
    http.get<any>(`${prefix}/notifications/my-page`, { params }),
  notificationDetail: (id: string) =>
    http.get<any>(`${prefix}/notifications/my-detail`, { params: { id } }),
  notificationUnreadCount: () => http.get<any>(`${prefix}/notifications/unread-count`),
  readNotifications: (ids: string[]) =>
    http.post<any>(`${prefix}/notifications/read`, { ids }),
  readAllNotifications: () => http.post<any>(`${prefix}/notifications/read-all`),
}
