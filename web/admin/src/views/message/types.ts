/** Author: Charlie */

export interface MessageAttachment {
  id: string
  message_id: string
  file_id: string | null
  name: string
  url: string
  content_type: string | null
  size: number | null
  attachment_type: string
  thumbnail_url: string | null
  duration: number | null
  width: number | null
  height: number | null
  sort: number
  extra: Record<string, any>
}

export interface Message {
  id: string
  conversation_id: string
  msg_type: string
  parent_id: string | null
  sender_type: string
  sender_account_type: string | null
  sender_account_id: string | null
  sender_name: string | null
  sender_avatar: string | null
  sender_nickname: string | null
  content: string
  content_type: string
  reply_count: number
  is_revoked: boolean
  revoked_at: string | null
  extra: Record<string, any>
  created_at: string
  attachments: MessageAttachment[]
}

export interface Member {
  id: string
  conversation_id: string
  account_type: string
  account_id: string
  role: string
  unread_count: number
  last_read_message_id: string | null
  last_read_at: string | null
  last_delivered_at: string | null
  is_muted: boolean
  is_pinned: boolean
  joined_at: string
  left_at: string | null
  extra: Record<string, any>
  profile_name: string | null
  profile_avatar: string | null
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface Conversation {
  id: string
  conversation_type: string
  title: string | null
  avatar: string | null
  group_id: string | null
  owner_account_type: string | null
  owner_account_id: string | null
  status: string
  last_message_id: string | null
  last_message_at: string | null
  extra: Record<string, any>
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
  unread_count: number
  members: Member[]
}

export interface Friend {
  friendship_id: string
  account_type: string
  account_id: string
  friend_account_type: string
  friend_account_id: string
  name: string | null
  nickname: string | null
  avatar: string | null
  signature: string | null
  remark: string | null
  friend_at: string
}

export interface Group {
  id: string
  name: string
  avatar: string | null
  description: string | null
  owner_account_type: string
  owner_account_id: string
  status: string
  join_mode: string
  max_members: number
  member_count: number
  extra: Record<string, any>
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
  is_member?: boolean
  has_pending_request?: boolean
}

export interface GroupMember {
  id: string
  group_id: string
  account_type: string
  account_id: string
  role: string
  nickname: string | null
  is_muted: boolean
  joined_at: string
  left_at: string | null
  extra: Record<string, any>
  profile_name: string | null
  profile_avatar: string | null
}

export interface Notification {
  id: string
  title: string
  content: string
  content_type: string
  category: string
  severity: string
  target_scope: string
  target_account_type: string | null
  target_account_id: string | null
  sender_account_type: string | null
  sender_account_id: string | null
  source_type: string | null
  source_id: string | null
  status: string
  publish_at: string | null
  revoked_at: string | null
  extra: Record<string, any>
  is_read: boolean
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface Announcement {
  id: string
  title: string
  content: string
  content_type: string
  severity: string
  target_scope: string
  target_account_type: string | null
  publish_locations: Record<string, any>
  is_pinned: boolean
  pinned_until: string | null
  sender_account_type: string | null
  sender_account_id: string | null
  status: string
  publish_at: string | null
  revoked_at: string | null
  expire_at: string | null
  view_count: number
  extra: Record<string, any>
  is_read: boolean
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface SearchUser {
  account_type: string
  account_id: string
  account: string | null
  name: string | null
  nickname: string | null
  avatar: string | null
  signature: string | null
  is_friend: boolean
  has_pending_request?: boolean
}

export interface FriendRequest {
  id: string
  applicant_type: string
  applicant_id: string
  applicant_name: string | null
  applicant_avatar: string | null
  recipient_type: string
  recipient_id: string
  recipient_name: string | null
  recipient_avatar: string | null
  message: string | null
  status: string
  handled_at: string | null
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface GroupJoinRequest {
  id: string
  group_id: string
  applicant_type: string
  applicant_id: string
  message: string | null
  status: string
  handled_by_type: string | null
  handled_by_id: string | null
  handled_at: string | null
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
  applicant_name: string | null
  applicant_avatar: string | null
  group_name: string | null
}

export interface Profile {
  account_type: string | null
  account_id: string | null
  name: string | null
  account: string | null
  nickname: string | null
  title: string | null
  department: string | null
  role: string | null
  signature: string | null
  phone: string | null
  email: string | null
  avatar: string | null
  avatarText: string
  statusText: string
}

export interface PageData<T> {
  records: T[]
  total: number
  current: number
  size: number
}
