<script setup lang="ts">
import { computed, onMounted, provide, reactive, ref, watch } from 'vue'
import { useThemeVars } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore, useAuthStore, useImCenterStore } from '@/stores'
import { messageApi } from '@/api'

const props = withDefaults(
  defineProps<{
    /** 弹窗模式：不改写 URL，关闭回到工作台 */
    modal?: boolean
  }>(),
  { modal: true },
)
import {
  type Message,
  type Conversation,
  type Friend,
  type Group,
  type Notification,
  type FriendRequest,
  type GroupJoinRequest,
} from './types'
import {
  MESSAGE_ACTIONS_KEY,
  MESSAGE_UI_STATE_KEY,
  MESSAGE_DATA_KEY,
  type MessageActions,
  type MessageUIState,
} from './provide-keys'
import { useWebSocket } from './use-websocket'

import Sidebar from './components/Sidebar.vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import ListPane from './components/ListPane.vue'
import ChatPane from './components/ChatPane.vue'
import NoticeDetail from './components/NoticeDetail.vue'
import ContactDetail from './components/ContactDetail.vue'
import ProfilePane from './components/ProfilePane.vue'
import ProfileModal from './components/ProfileModal.vue'
import AddFriendModal from './components/AddFriendModal.vue'
import CreateGroupModal from './components/CreateGroupModal.vue'

const appStore = useAppStore()
const themeVars = useThemeVars()
const router = useRouter()
const route = useRoute()
const homePath = import.meta.env.VITE_HOME_PATH || '/dashboard'
const authStore = useAuthStore()
const imCenterStore = useImCenterStore()

/* ---- Page data ---- */

const data = reactive({
  conversations: [] as Conversation[],
  friends: [] as Friend[],
  groups: [] as Group[],
  messagesByConversation: {} as Record<string, Message[]>,
  notices: [] as Notification[],
  friendRequests: [] as FriendRequest[],
  groupJoinRequests: [] as GroupJoinRequest[],
  pendingGroupJoinRequests: [] as GroupJoinRequest[],
  profile: null as any,
})

/* ---- URL-driven state ---- */

const activeSection = ref('chat')
const mobileView = ref('list')
const selectedConversationId = ref('')
const selectedContact = ref<{ kind: string; id: string } | null>(null)
const selectedNoticeId = ref<string | null>(null)
const selectedPendingRequestId = ref<string | null>(null)
const showAddModal = ref(false)
const addModalMode = ref<'friend' | 'group'>('friend')
const showCreateGroupModal = ref(false)
const conversationDrafts = ref<Record<string, { text: string; attachments: any[] }>>({})
const searchText = ref('')
const searchScope = ref('conversations')
const contactTab = ref('friends')
const noticeTab = ref('notices')

/* ---- Derived UI state ---- */

const showProfileModal = ref(false)
const contactActionHint = ref('')
/** 弹窗仅 PC 三栏布局，不再走移动端响应式 */
const isMobile = computed(() => (props.modal ? false : appStore.isMobile))
const hasSearchKeyword = computed(() => searchText.value.trim().length > 0)

const selectedConversation = computed(
  () => data.conversations.find((c) => c.id === selectedConversationId.value) ?? null,
)

const selectedNotice = computed(
  () => data.notices.find((n) => n.id === selectedNoticeId.value) ?? null,
)

const selectedPendingRequest = computed(
  () =>
    [...data.friendRequests, ...data.groupJoinRequests, ...data.pendingGroupJoinRequests].find(
      (r) => r.id === selectedPendingRequestId.value,
    ) ?? null,
)

const showPendingDetail = computed(
  () =>
    (activeSection.value === 'notice' && selectedNoticeId.value !== null) ||
    selectedPendingRequestId.value !== null,
)

const showListPane = computed(
  () => activeSection.value !== 'profile' && (!isMobile.value || mobileView.value === 'list'),
)
const showChatPane = computed(
  () =>
    activeSection.value === 'chat' &&
    (!isMobile.value || mobileView.value === 'chat') &&
    selectedConversation.value,
)
const showNoticeDetailPane = computed(
  () => showPendingDetail.value && activeSection.value === 'notice',
)
const showContactDetailPane = computed(
  () =>
    activeSection.value === 'contacts' &&
    (!isMobile.value || mobileView.value === 'detail') &&
    selectedContact.value,
)
const showProfilePane = computed(() => isMobile.value && activeSection.value === 'profile')

const selectedFriendContact = computed(() => {
  if (selectedContact.value?.kind !== 'friend') return null
  return (
    data.friends.find(
      (f) =>
        f.friendship_id === selectedContact.value?.id ||
        f.friend_account_id === selectedContact.value?.id,
    ) ?? null
  )
})
const selectedGroupContact = computed(() => {
  if (selectedContact.value?.kind !== 'group') return null
  return data.groups.find((g) => g.id === selectedContact.value?.id) ?? null
})

/* ---- URL sync helpers ---- */

function syncStateToUrl() {
  if (props.modal) return
  const query: Record<string, string> = {}
  if (activeSection.value !== 'chat') query.section = activeSection.value
  if (selectedConversationId.value) query.conversation = selectedConversationId.value
  if (selectedContact.value) {
    query.contactKind = selectedContact.value.kind
    query.contactId = selectedContact.value.id
  }
  if (selectedNoticeId.value) query.notice = selectedNoticeId.value
  if (selectedPendingRequestId.value) query.pending = selectedPendingRequestId.value
  if (contactTab.value !== 'friends') query.ctab = contactTab.value
  if (noticeTab.value !== 'notices') query.ntab = noticeTab.value
  if (isMobile.value && mobileView.value !== 'list') query.view = mobileView.value
  router.replace({ query }).catch(() => {})
}

function applyFromRoute() {
  const q = route.query
  activeSection.value = (q.section as string) || 'chat'
  selectedConversationId.value = (q.conversation as string) || ''
  selectedContact.value =
    q.contactKind && q.contactId
      ? { kind: q.contactKind as string, id: q.contactId as string }
      : null
  selectedNoticeId.value = (q.notice as string) || null
  selectedPendingRequestId.value = (q.pending as string) || null
  contactTab.value = (q.ctab as string) || 'friends'
  noticeTab.value = (q.ntab as string) || 'notices'
  if (isMobile.value) {
    if (q.view) {
      mobileView.value = q.view as string
    } else if (selectedConversationId.value && activeSection.value === 'chat') {
      mobileView.value = 'chat'
    } else {
      mobileView.value = 'list'
    }
  }
}

watch(
  [
    activeSection,
    selectedConversationId,
    selectedContact,
    selectedNoticeId,
    selectedPendingRequestId,
    mobileView,
    contactTab,
    noticeTab,
  ],
  syncStateToUrl,
  { flush: 'post' },
)

watch(
  () => route.query,
  () => {
    if (!props.modal) applyFromRoute()
  },
)

/* ---- WebSocket ---- */

const ws = useWebSocket({
  onNewMessage(msgData) {
    const convId = msgData.conversation_id
    if (!convId) return
    if (!data.messagesByConversation[convId]) {
      data.messagesByConversation[convId] = []
    }
    // 去重：防止 REST 响应和 WS 同时到达导致重复；换新数组以触发依赖 length/尾部的 watch
    const msgs = data.messagesByConversation[convId]
    if (!msgs.some((m: any) => m.id === msgData.id)) {
      data.messagesByConversation[convId] = [...msgs, msgData]
    }
    const conv = data.conversations.find((c) => c.id === convId)
    if (conv) {
      conv.last_message_id = msgData.id
      conv.last_message_at = msgData.created_at
      if (conv.id !== selectedConversationId.value) {
        conv.unread_count = (conv.unread_count || 0) + 1
      }
    }
    // Mark read if currently viewing this conversation
    if (convId === selectedConversationId.value && msgData.id) {
      ws.markConversationRead(convId, msgData.id)
    }
  },
  onOfflineMessages(messages) {
    for (const item of messages) {
      // item 可能是离线队列包装对象 { event_type, conversation_id, message_id, event_payload }
      // 也可能是已解包的消息数据（适配两种格式）
      const msg = item.event_payload?.data ?? item
      if (!msg) continue
      const convId = msg.conversation_id || item.conversation_id
      if (!convId) continue
      if (!data.messagesByConversation[convId]) {
        data.messagesByConversation[convId] = []
      }
      // 去重：离线消息可能和已有的 REST/WS 消息重复
      const existing = data.messagesByConversation[convId]
      const existingIds = new Set(existing.map((m: any) => m.id))
      if (!existingIds.has(msg.id)) {
        data.messagesByConversation[convId] = [...existing, msg]
      }
      const conv = data.conversations.find((c) => c.id === convId)
      if (conv) {
        conv.last_message_id = msg.id
        conv.last_message_at = msg.created_at
        if (conv.id !== selectedConversationId.value) {
          conv.unread_count = (conv.unread_count || 0) + 1
        }
      }
    }
  },
  onNewNotification(notificationData) {
    // 实时收到新通知，插入 notices 列表头部
    if (notificationData && notificationData.id) {
      if (!data.notices.some((n: any) => n.id === notificationData.id)) {
        data.notices.unshift(notificationData)
      }
    }
  },
  onNewFriendRequest(reqData) {
    if (reqData && reqData.id) {
      if (!data.friendRequests.some((r: any) => r.id === reqData.id)) {
        data.friendRequests.unshift({
          ...reqData,
          applicant_name: reqData.applicant_name || null,
          applicant_avatar: reqData.applicant_avatar || null,
          status: reqData.status || 'PENDING',
        })
      }
    } else {
      messageApi
        .myFriendRequests()
        .then((res: any) => {
          if (res?.data) data.friendRequests = res.data
        })
        .catch(() => {})
    }
  },
  onNewJoinRequest(reqData) {
    // 收到新的入群申请，插入 pendingGroupJoinRequests 列表头部（去重）
    if (reqData && reqData.id) {
      if (!data.pendingGroupJoinRequests.some((r: any) => r.id === reqData.id)) {
        // 补充必要字段前端展示
        data.pendingGroupJoinRequests.unshift({
          ...reqData,
          applicant_name: reqData.applicant_name || null,
          applicant_avatar: reqData.applicant_avatar || null,
          group_name: reqData.group_name || null,
        })
      }
    }
  },
  onJoinRequestHandled(result) {
    // 自己的入群申请被处理，更新状态
    const req = data.groupJoinRequests.find((r: any) => r.id === result.request_id)
    if (req) {
      req.status = result.status
    } else {
      // 可能还没加载到本地，重新加载
      messageApi
        .myJoinRequests()
        .then((res: any) => {
          if (res?.data) data.groupJoinRequests = res.data
        })
        .catch(() => {})
    }
  },
})

/* ---- Actions ---- */

function goHome() {
  if (props.modal) {
    imCenterStore.close()
    return
  }
  router.push(homePath)
}
function openProfileModal() {
  showProfileModal.value = true
}
function goProfileCenter() {
  showProfileModal.value = false
  router.push('/usercenter')
}
function handleLogout() {
  authStore.logout()
}

function openChatSection() {
  activeSection.value = 'chat'
  selectedConversationId.value = ''
  if (isMobile.value) mobileView.value = 'list'
}
function openContactsSection() {
  activeSection.value = 'contacts'
  if (isMobile.value) mobileView.value = 'list'
}
function openNoticeSection() {
  activeSection.value = 'notice'
  if (isMobile.value) mobileView.value = 'list'
}
function openProfileSection() {
  activeSection.value = 'profile'
  if (isMobile.value) mobileView.value = 'list'
}

function openFriend(friend: Friend) {
  contactActionHint.value = ''
  selectedContact.value = { kind: 'friend', id: friend.friendship_id }
  selectedNoticeId.value = null
  selectedPendingRequestId.value = null
  activeSection.value = 'contacts'
  if (isMobile.value) mobileView.value = 'detail'
}
function openGroup(group: Group) {
  contactActionHint.value = ''
  selectedContact.value = { kind: 'group', id: group.id }
  selectedNoticeId.value = null
  selectedPendingRequestId.value = null
  activeSection.value = 'contacts'
  if (isMobile.value) mobileView.value = 'detail'
}

function openConversation(conversationId: string) {
  const conv = data.conversations.find((c) => c.id === conversationId)
  if (!conv) {
    // 会话不在本地列表中 — 从服务端重新加载
    messageApi
      .conversationList()
      .then((res) => {
        const list = res?.data?.records
        if (list) {
          data.conversations = list
          const found = list.find((c: any) => c.id === conversationId)
          if (found) {
            selectedConversationId.value = conversationId
            selectedContact.value = null
            selectedNoticeId.value = null
            selectedPendingRequestId.value = null
            activeSection.value = 'chat'
            if (isMobile.value) mobileView.value = 'chat'
            found.unread_count = 0
          }
        }
      })
      .catch(() => {
        window.$message?.error?.('加载会话失败')
      })
    // 即使是新会话也尝试标记已读
    messageApi.markConversationRead({ id: conversationId }).catch(() => {})
    return
  }
  selectedConversationId.value = conversationId
  selectedContact.value = null
  selectedNoticeId.value = null
  selectedPendingRequestId.value = null
  activeSection.value = 'chat'
  if (isMobile.value) mobileView.value = 'chat'
  conv.unread_count = 0
  // 调用 API 持久化已读状态
  messageApi.markConversationRead({ id: conversationId }).catch(() => {})
}

function saveDraft(draft: { text: string; attachments: any[] }) {
  if (selectedConversationId.value) conversationDrafts.value[selectedConversationId.value] = draft
}
function closeCurrentConversation() {
  selectedConversationId.value = ''
  selectedContact.value = null
  if (isMobile.value) mobileView.value = 'list'
}

function backToListPane() {
  if (isMobile.value) mobileView.value = 'list'
}
function openAddModal(mode?: 'friend' | 'group') {
  addModalMode.value = mode || 'friend'
  showAddModal.value = true
}

function openNoticeDetail(notice: Notification) {
  messageApi.readNotification({ ids: [notice.id] }).catch(() => {})
  selectedNoticeId.value = notice.id
  selectedPendingRequestId.value = null
  selectedContact.value = null
  if (isMobile.value) mobileView.value = 'detail'
}
function openPendingDetail(request: FriendRequest | GroupJoinRequest) {
  selectedPendingRequestId.value = request.id
  selectedNoticeId.value = null
  selectedContact.value = null
  if (isMobile.value) mobileView.value = 'detail'
}
function closePendingDetail() {
  selectedNoticeId.value = null
  selectedPendingRequestId.value = null
  if (isMobile.value) mobileView.value = 'list'
}

const canHandleSelectedRequest = computed(() => {
  const req = selectedPendingRequest.value
  if (!req) return false
  if ('group_id' in req) {
    // 群聊申请：只对 pendingGroupJoinRequests 列表中的可处理
    return data.pendingGroupJoinRequests.some((r) => r.id === req.id)
  }
  // 好友申请：只有接收人才能处理
  return (
    req.recipient_type === data.profile?.account_type &&
    req.recipient_id === data.profile?.account_id
  )
})

async function acceptPendingRequest() {
  const req = selectedPendingRequest.value
  if (!req) return
  try {
    if ('group_id' in req) {
      await messageApi.handleJoinGroupRequest({ id: req.id, status: 'ACCEPTED' })
      const idx = data.pendingGroupJoinRequests.findIndex((r) => r.id === req.id)
      if (idx >= 0) {
        const req_item = data.pendingGroupJoinRequests.splice(idx, 1)[0]
        req_item.status = 'ACCEPTED'
        data.groupJoinRequests.push(req_item)
      }
    } else {
      await messageApi.handleFriendRequest({ request_id: req.id, action: 'ACCEPT' })
      const req_item = data.friendRequests.find((r: any) => r.id === req.id)
      if (req_item) req_item.status = 'ACCEPTED'
    }
  } catch {
    window.$message?.error?.('操作失败')
  }
  closePendingDetail()
}
async function rejectPendingRequest() {
  const req = selectedPendingRequest.value
  if (!req) return
  try {
    if ('group_id' in req) {
      await messageApi.handleJoinGroupRequest({ id: req.id, status: 'REJECTED' })
      const idx = data.pendingGroupJoinRequests.findIndex((r) => r.id === req.id)
      if (idx >= 0) {
        const req_item = data.pendingGroupJoinRequests.splice(idx, 1)[0]
        req_item.status = 'REJECTED'
        data.groupJoinRequests.push(req_item)
      }
    } else {
      await messageApi.handleFriendRequest({ request_id: req.id, action: 'REJECT' })
      const req_item = data.friendRequests.find((r: any) => r.id === req.id)
      if (req_item) req_item.status = 'REJECTED'
    }
  } catch {
    window.$message?.error?.('操作失败')
  }
  closePendingDetail()
}

async function continueChatFromContact() {
  if (selectedFriendContact.value) {
    const friend = selectedFriendContact.value
    let friendConv = data.conversations.find(
      (c) =>
        c.conversation_type === 'DIRECT' &&
        c.members?.some(
          (m) =>
            m.account_id === friend.friend_account_id &&
            m.account_type === friend.friend_account_type,
        ),
    )
    if (friendConv) {
      openConversation(friendConv.id)
      return
    }

    // Create direct conversation on demand
    try {
      const res = await messageApi.createDirectConversation({
        account_type: friend.friend_account_type,
        account_id: friend.friend_account_id,
      })
      if (res?.data) {
        data.conversations.unshift(res.data)
        openConversation(res.data.id)
        return
      }
      // Response succeeded but no data — reload list and retry
      const convRes = await messageApi.conversationList()
      if (convRes?.data?.records) {
        data.conversations = convRes.data.records
        friendConv = data.conversations.find(
          (c) =>
            c.conversation_type === 'DIRECT' &&
            c.members?.some(
              (m) =>
                m.account_id === friend.friend_account_id &&
                m.account_type === friend.friend_account_type,
            ),
        )
        if (friendConv) {
          openConversation(friendConv.id)
          return
        }
      }
      window.$message?.error?.('创建会话失败')
    } catch {
      window.$message?.error?.('创建会话失败')
    }
    return
  }
  if (selectedGroupContact.value) {
    const group = selectedGroupContact.value
    let groupConv = data.conversations.find((c) => c.group_id === group.id)
    if (groupConv) {
      openConversation(groupConv.id)
      return
    }

    // Reload conversations and try again
    try {
      const convRes = await messageApi.conversationList()
      if (convRes?.data?.records) {
        data.conversations = convRes.data.records
        groupConv = data.conversations.find((c) => c.group_id === group.id)
        if (groupConv) {
          openConversation(groupConv.id)
          return
        }
      }
      window.$message?.error?.('未找到群聊会话')
    } catch {
      window.$message?.error?.('未找到群聊会话')
    }
  }
}

async function handleRemoveFriend() {
  const f = selectedFriendContact.value
  if (!f) return
  contactActionHint.value = ''
  try {
    await messageApi.removeFriend({ friendship_id: f.friendship_id })
    const idx = data.friends.findIndex((x) => x.friendship_id === f.friendship_id)
    if (idx >= 0) data.friends.splice(idx, 1)
    selectedContact.value = null
    window.$message?.success?.('已删除好友')
  } catch {
    window.$message?.error?.('删除好友失败')
  }
}

async function handleLeaveGroup() {
  const g = selectedGroupContact.value
  if (!g) return
  contactActionHint.value = ''
  try {
    await messageApi.leaveGroup({ id: g.id })
    const idx = data.groups.findIndex((x) => x.id === g.id)
    if (idx >= 0) data.groups.splice(idx, 1)
    selectedContact.value = null
    window.$message?.success?.('已退出群聊')
  } catch {
    window.$message?.error?.('退出群聊失败')
  }
}

async function handleDissolveGroup() {
  const g = selectedGroupContact.value
  if (!g) return
  contactActionHint.value = ''
  try {
    await messageApi.dissolveGroup({ id: g.id })
    const idx = data.groups.findIndex((x) => x.id === g.id)
    if (idx >= 0) data.groups.splice(idx, 1)
    data.conversations = data.conversations.filter((c) => c.group_id !== g.id)
    selectedContact.value = null
    if (selectedConversationId.value) {
      const cur = data.conversations.find((c) => c.id === selectedConversationId.value)
      if (!cur) closeCurrentConversation()
    }
    window.$message?.success?.('已解散群聊')
  } catch {
    window.$message?.error?.('解散群聊失败')
  }
}

const messageActions: MessageActions = {
  goHome,
  openProfileModal,
  goProfileCenter,
  handleLogout,
  openConversation,
  closeCurrentConversation,
  openChatSection,
  openContactsSection,
  openNoticeSection,
  openProfileSection,
  backToListPane,
  openFriend,
  openGroup,
  openNoticeDetail,
  openPendingDetail,
  closePendingDetail,
  openAddModal,
  acceptPendingRequest,
  rejectPendingRequest,
  continueChatFromContact,
  handleRemoveFriend,
  handleLeaveGroup,
  handleDissolveGroup,
}
const messageUIState: MessageUIState = {
  activeSection,
  isMobile,
  mobileView,
  showProfileModal,
  searchText,
  hasSearchKeyword,
  searchScope,
  contactTab,
  noticeTab,
  selectedNoticeId,
  selectedPendingRequestId,
}

provide(MESSAGE_ACTIONS_KEY, messageActions)
provide(MESSAGE_UI_STATE_KEY, messageUIState)
provide(MESSAGE_DATA_KEY, data)

onMounted(async () => {
  try {
    const [
      meRes,
      convRes,
      friendRes,
      groupRes,
      noticeRes,
      reqRes,
      joinReqRes,
      pendingGroupJoinRes,
    ] = await Promise.all([
      import('@/api/auth').then((m) => m.me()).catch(() => null),
      messageApi.conversationList().catch(() => null),
      messageApi.friendList().catch(() => null),
      messageApi.groupList().catch(() => null),
      messageApi.notificationMyPage({ current: 1, size: 50 }).catch(() => null),
      messageApi.myFriendRequests().catch(() => null),
      messageApi.myJoinRequests().catch(() => null),
      messageApi.pendingJoinRequests().catch(() => null),
    ])

    const me = meRes?.data
    if (me) {
      data.profile = {
        account_type: me.account_type ?? '',
        account_id: me.account_id ?? '',
        name: me.name ?? '',
        account: me.account ?? '',
        nickname: me.nickname ?? me.name ?? '',
        title: me.profile?.title ?? '',
        department: me.dept_id_names?.map((d: any) => d.name).join('、') ?? '',
        role: me.role_id_names?.map((r: any) => r.name).join('、') ?? '',
        signature: me.profile?.signature ?? '',
        phone: me.profile?.phone ?? '',
        email: me.profile?.email ?? '',
        avatar: me.profile?.avatar ?? me.avatar ?? '',
        avatarText: (me.nickname ?? me.name ?? '?').charAt(0),
        statusText: '在线',
      }
    }
    if (convRes?.data?.records) data.conversations = convRes.data.records
    if (friendRes?.data) data.friends = friendRes.data
    if (groupRes?.data) data.groups = groupRes.data
    if (noticeRes?.data?.records) {
      data.notices = noticeRes.data.records.map((n: any) => ({
        ...n,
        is_read: n.is_read ?? false,
        severity: (n.severity ?? 'INFO').toLowerCase(),
      }))
    }
    if (reqRes?.data) data.friendRequests = reqRes.data
    if (joinReqRes?.data) data.groupJoinRequests = joinReqRes.data
    if (pendingGroupJoinRes?.data) data.pendingGroupJoinRequests = pendingGroupJoinRes.data

    if (props.modal) {
      activeSection.value = imCenterStore.initialSection || 'chat'
      const cid = imCenterStore.initialConversationId
      if (cid) {
        selectedConversationId.value = cid
        openConversation(cid)
      }
    } else {
      applyFromRoute()
      if (selectedConversationId.value) {
        openConversation(selectedConversationId.value)
      }
    }
  } catch {
    // silent
  }

  ws.connect()
})

watch(
  () => [imCenterStore.visible, imCenterStore.initialConversationId, imCenterStore.initialSection] as const,
  ([visible, cid, section]) => {
    if (!props.modal || !visible) return
    if (section) activeSection.value = section
    if (cid) {
      selectedConversationId.value = cid
      void openConversation(cid)
    }
  },
)

const pageStyle = computed(() => ({
  backgroundColor: themeVars.value.bodyColor,
  color: themeVars.value.textColorBase,
  height: props.modal ? '100%' : '100dvh',
  minHeight: props.modal ? '100%' : '100vh',
  maxHeight: props.modal ? '100%' : undefined,
}))
</script>

<template>
  <n-el
    tag="main"
    class="flex flex-col overflow-hidden"
    :class="props.modal ? 'h-full max-h-full min-h-0' : 'fixed inset-0'"
    :style="pageStyle"
  >
    <div
      class="grid min-h-0 flex-1 gap-0 overflow-hidden"
      :class="
        props.modal
          ? 'grid-cols-[60px_300px_minmax(0,1fr)]'
          : 'md:grid-cols-[60px_minmax(280px,360px)_minmax(0,1fr)]'
      "
    >
      <Sidebar />

      <ListPane v-show="showListPane" />

      <ChatPane
        v-if="showChatPane"
        :conversation="selectedConversation!"
        :draft="conversationDrafts[selectedConversationId] || { text: '', attachments: [] }"
        @update:draft="saveDraft($event)"
        @close="closeCurrentConversation"
      />

      <NoticeDetail
        v-show="showNoticeDetailPane"
        :request="selectedPendingRequest"
        :notice="selectedNotice"
        :can-handle="canHandleSelectedRequest"
        @accept-request="acceptPendingRequest"
        @reject-request="rejectPendingRequest"
        @close="closePendingDetail"
      />

      <ContactDetail
        v-show="showContactDetailPane"
        :friend="selectedFriendContact"
        :group="selectedGroupContact"
        :hint="contactActionHint"
        @chat="continueChatFromContact"
        @remove-friend="handleRemoveFriend"
        @leave-group="handleLeaveGroup"
        @dissolve-group="handleDissolveGroup"
        @back="backToListPane"
      />

      <ProfilePane v-show="showProfilePane" />
    </div>

    <MobileBottomNav v-if="!props.modal" />

    <ProfileModal />
    <AddFriendModal v-model:show="showAddModal" :initial-mode="addModalMode" />
    <CreateGroupModal v-model:show="showCreateGroupModal" />
  </n-el>
</template>

<style scoped>
.message-list-item {
  min-width: 0;
  overflow: hidden;
}
.message-list-item :deep(.n-list-item__main) {
  width: 100%;
  min-width: 0;
  overflow: hidden;
}
.message-list-row,
.message-list-main-line,
.message-list-sub-line {
  width: 100%;
  min-width: 0;
  overflow: hidden;
}
.message-list-body {
  min-width: 0;
  flex: 1 1 0;
  overflow: hidden;
}
.message-ellipsis {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
