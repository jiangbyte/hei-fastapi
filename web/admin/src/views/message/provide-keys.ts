import type { InjectionKey, Ref } from 'vue'
import type {
  Friend,
  Group,
  FriendRequest,
  GroupJoinRequest,
  Notification,
  Conversation,
} from './types'

export interface MessageActions {
  goHome: () => void
  openProfileModal: () => void
  goProfileCenter: () => void
  handleLogout: () => void
  openConversation: (conversationId: string) => void
  closeCurrentConversation: () => void
  openChatSection: () => void
  openContactsSection: () => void
  openNoticeSection: () => void
  openProfileSection: () => void
  backToListPane: () => void
  openFriend: (friend: Friend) => void
  openGroup: (group: Group) => void
  openNoticeDetail: (notice: Notification) => void
  openPendingDetail: (request: FriendRequest | GroupJoinRequest) => void
  closePendingDetail: () => void
  openAddModal: (mode?: 'friend' | 'group') => void
  acceptPendingRequest: () => void
  rejectPendingRequest: () => void
  continueChatFromContact: () => void
  handleRemoveFriend: () => void
  handleLeaveGroup: () => void
  handleDissolveGroup: () => void
}

export interface MessageUIState {
  activeSection: Ref<string>
  isMobile: Ref<boolean>
  mobileView: Ref<string>
  showProfileModal: Ref<boolean>
  searchText: Ref<string>
  hasSearchKeyword: Ref<boolean>
  searchScope: Ref<string>
  contactTab: Ref<string>
  noticeTab: Ref<string>
  selectedNoticeId: Ref<string | null>
  selectedPendingRequestId: Ref<string | null>
}

export const MESSAGE_ACTIONS_KEY: InjectionKey<MessageActions> = Symbol('message-actions')
export const MESSAGE_UI_STATE_KEY: InjectionKey<MessageUIState> = Symbol('message-ui-state')

import type { Message } from './types'
export const MESSAGE_DATA_KEY: InjectionKey<{
  conversations: Conversation[]
  friends: Friend[]
  groups: Group[]
  messagesByConversation: Record<string, Message[]>
  notices: Notification[]
  friendRequests: FriendRequest[]
  groupJoinRequests: GroupJoinRequest[]
  pendingGroupJoinRequests: GroupJoinRequest[]
  profile: any
}> = Symbol('message-data')
