import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  Empty,
  Grid,
  Image,
  Input,
  Modal,
  Segmented,
  Select,
  Space,
  Spin,
  Tag,
  Tooltip,
  message,
} from 'antd'
import type { MenuProps } from 'antd'
import {
  ArrowLeftOutlined,
  BellOutlined,
  MessageOutlined,
  PaperClipOutlined,
  PlusOutlined,
  SendOutlined,
  TeamOutlined,
  UserAddOutlined,
  UserOutlined,
  UsergroupAddOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'

const { useBreakpoint } = Grid
import { useImWebSocket } from '@/hooks/useImWebSocket'
import { useAuthStore } from '@/stores/auth'
import { useImUnreadStore } from '@/stores/imUnread'
import { isImageFile, resolveFileUrl } from '@/utils/file'
import { formatDateTime } from '@/utils/time'
import { fileApi, imApi } from '@/api'

type PendingAttachment = {
  name: string
  size: number
  type: string
  file: File
}

function formatFileSize(size?: number | null) {
  if (size == null || Number.isNaN(size)) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function unwrapOfflineMessage(item: any): any | null {
  const msg = item?.event_payload?.data ?? item?.data ?? item
  if (!msg?.id || !msg?.conversation_id) return null
  return msg as any
}

function typeLabel(accountType: string) {
  return accountType === 'PORTAL' ? '学生' : '管理员'
}

/** 与 Admin ContactList 一致：name → nickname */
function friendListName(friend: Pick<any, 'name' | 'nickname'>) {
  return friend.name || friend.nickname || '未知'
}

function displayName(parts: {
  name?: string | null
  nickname?: string | null
  remark?: string | null
  fallback?: string
}) {
  return parts.remark || parts.nickname || parts.name || parts.fallback || '未命名'
}

function messagePreviewText(msg: Pick<any, 'content' | 'sender_nickname' | 'sender_name'>) {
  const prefix =
    msg.sender_nickname || msg.sender_name
      ? `${msg.sender_nickname || msg.sender_name}：`
      : ''
  const body = (msg.content || '').trim() || '[附件]'
  return `${prefix}${body}`
}

function conversationPreview(
  conv: any,
  opts?: { activeId?: string | null; messages?: any[] },
) {
  const activeMessages = opts?.messages
  if (opts?.activeId === conv.id && activeMessages?.length) {
    return messagePreviewText(activeMessages[activeMessages.length - 1])
  }
  if (conv.last_message?.trim()) return conv.last_message.trim()
  return conv.title || '会话'
}

function sortConversations(list: any[]) {
  return [...list].sort((a, b) => {
    const ta = a.last_message_at ?? a.created_at ?? ''
    const tb = b.last_message_at ?? b.created_at ?? ''
    return new Date(tb).getTime() - new Date(ta).getTime()
  })
}

export function MessagesPage() {
  const screens = useBreakpoint()
  const isMobile = !screens.md
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const isLogin = useAuthStore((s) => s.isLogin)
  const userInfo = useAuthStore((s) => s.userInfo)
  const myType = userInfo?.accountType || 'PORTAL'
  const myId = userInfo?.accountId || ''
  const myAvatar = resolveFileUrl(userInfo?.avatar)
  const myName = userInfo?.nickname || userInfo?.name || '?'

  const [loading, setLoading] = useState(true)
  const [conversations, setConversations] = useState<any[]>([])
  const [friends, setFriends] = useState<any[]>([])
  const [groups, setGroups] = useState<any[]>([])
  const [requests, setRequests] = useState<any[]>([])
  const [myJoinRequests, setMyJoinRequests] = useState<any[]>([])
  const [pendingJoinRequests, setPendingJoinRequests] = useState<any[]>([])
  const [notices, setNotices] = useState<any[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [selectedNoticeId, setSelectedNoticeId] = useState<string | null>(null)
  const [selectedRequest, setSelectedRequest] = useState<
    | { kind: 'friend'; data: any }
    | { kind: 'group'; data: any }
    | null
  >(null)
  /** 移动端 IM 分层：列表层 / 会话层，不同时上下堆叠 */
  const [mobilePane, setMobilePane] = useState<'list' | 'chat'>('list')
  const [messages, setMessages] = useState<any[]>([])
  const [msgLoading, setMsgLoading] = useState(false)
  const [draft, setDraft] = useState('')
  const [pendingFiles, setPendingFiles] = useState<PendingAttachment[]>([])
  const [sending, setSending] = useState(false)
  /** 与 Admin 侧边栏一致：聊天 / 通讯录 / 通知 */
  const [activeSection, setActiveSection] = useState<'chat' | 'contacts' | 'notice'>('chat')
  const [contactTab, setContactTab] = useState<'friends' | 'groups'>('friends')
  const [noticeTab, setNoticeTab] = useState<'notices' | 'requests'>('notices')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const activeIdRef = useRef<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const [addOpen, setAddOpen] = useState(false)
  const [addMode, setAddMode] = useState<'friend' | 'group'>('friend')
  const [searchKw, setSearchKw] = useState('')
  const [searchHits, setSearchHits] = useState<any[]>([])
  const [groupHits, setGroupHits] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  const [createGroupOpen, setCreateGroupOpen] = useState(false)
  const [groupName, setGroupName] = useState('')
  const [groupDesc, setGroupDesc] = useState('')
  const [groupInvitees, setGroupInvitees] = useState<string[]>([])
  const [creatingGroup, setCreatingGroup] = useState(false)

  const [groupManageId, setGroupManageId] = useState<string | null>(null)
  const [groupMembers, setGroupMembers] = useState<any[]>([])

  const refreshUnread = useImUnreadStore((s) => s.refresh)

  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) || null,
    [conversations, activeId],
  )

  const isIncomingFriend = useCallback(
    (r: any) => r.recipient_type === myType && r.recipient_id === myId,
    [myType, myId],
  )

  const incomingPendingCount = useMemo(
    () =>
      requests.filter((r) => isIncomingFriend(r) && r.status === 'PENDING').length +
      pendingJoinRequests.filter((r) => r.status === 'PENDING').length,
    [requests, pendingJoinRequests, isIncomingFriend],
  )

  const unreadNoticeCount = useMemo(
    () => notices.filter((n) => !n.is_read).length,
    [notices],
  )

  const noticeBadgeTotal = unreadNoticeCount + incomingPendingCount

  const combinedGroupJoinRequests = useMemo(() => {
    const map = new Map<string, any>()
    for (const r of [...myJoinRequests, ...pendingJoinRequests]) {
      map.set(r.id, r)
    }
    return [...map.values()].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  }, [myJoinRequests, pendingJoinRequests])

  const selectedNotice = useMemo(
    () => notices.find((n) => n.id === selectedNoticeId) || null,
    [notices, selectedNoticeId],
  )

  const canHandleSelectedRequest = useMemo(() => {
    if (!selectedRequest || selectedRequest.data.status !== 'PENDING') return false
    if (selectedRequest.kind === 'friend') return isIncomingFriend(selectedRequest.data)
    return pendingJoinRequests.some((r) => r.id === selectedRequest.data.id)
  }, [selectedRequest, isIncomingFriend, pendingJoinRequests])

  const reloadLists = useCallback(async () => {
    const [convRes, friendRes, groupRes, reqRes, noticeRes, myJoinRes, pendingJoinRes] =
      await Promise.all([
        imApi.conversationList({ current: 1, size: 50 }),
        imApi.friendList(),
        imApi.groupList(),
        imApi.myFriendRequests(),
        imApi.notificationPage({ current: 1, size: 50 }),
        imApi.myJoinRequests(),
        imApi.pendingJoinRequests(),
      ])
    setConversations(sortConversations(convRes.data.records ?? []))
    setFriends(friendRes.data ?? [])
    setGroups(groupRes.data ?? [])
    setRequests(reqRes.data ?? [])
    setNotices(
      (noticeRes.data.records ?? []).map((n: any) => ({
        ...n,
        is_read: n.is_read ?? false,
        severity: String(n.severity || 'INFO').toLowerCase(),
      })),
    )
    setMyJoinRequests(myJoinRes.data ?? [])
    setPendingJoinRequests(pendingJoinRes.data ?? [])
    void refreshUnread()
  }, [refreshUnread])

  const sortedConversations = useMemo(
    () => sortConversations(conversations),
    [conversations],
  )

  const totalUnreadCount = useMemo(
    () => conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0),
    [conversations],
  )

  const openSection = useCallback((section: 'chat' | 'contacts' | 'notice') => {
    setActiveSection(section)
    setMobilePane('list')
    if (section === 'notice') {
      setSelectedNoticeId(null)
      setSelectedRequest(null)
    }
  }, [])

  const contactAddMenu: MenuProps['items'] = [
    {
      key: 'add-friend',
      icon: <UserAddOutlined />,
      label: '添加好友',
      onClick: () => {
        setAddOpen(true)
        setAddMode('friend')
        setSearchHits([])
        setGroupHits([])
        setSearchKw('')
      },
    },
    {
      key: 'join-group',
      icon: <UsergroupAddOutlined />,
      label: '添加群聊',
      onClick: () => {
        setAddOpen(true)
        setAddMode('group')
        setSearchHits([])
        setGroupHits([])
        setSearchKw('')
      },
    },
    {
      key: 'create-group',
      icon: <PlusOutlined />,
      label: '创建群聊',
      onClick: () => setCreateGroupOpen(true),
    },
  ]

  useEffect(() => {
    if (!isLogin()) return
    let mounted = true
    void (async () => {
      setLoading(true)
      try {
        await reloadLists()
      } catch {
        if (mounted) message.error('加载消息失败')
      } finally {
        if (mounted) setLoading(false)
      }
    })()
    return () => {
      mounted = false
    }
  }, [isLogin, reloadLists])

  const openConversation = useCallback(async (conversationId: string) => {
    setSelectedNoticeId(null)
    setSelectedRequest(null)
    setActiveId(conversationId)
    activeIdRef.current = conversationId
    setActiveSection('chat')
    setMobilePane('chat')
    setPendingFiles([])
    setMsgLoading(true)
    try {
      const res = await imApi.messagePage({ conversation_id: conversationId, current: 1, size: 50 })
      const records = [...(res.data.records ?? [])].reverse()
      setMessages(records)
      await imApi.markConversationRead({ id: conversationId })
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, unread_count: 0 } : c)),
      )
      void refreshUnread()
    } catch {
      message.error('加载聊天记录失败')
    } finally {
      setMsgLoading(false)
    }
  }, [refreshUnread])

  const conversationFromQuery = searchParams.get('conversation')

  useEffect(() => {
    if (!conversationFromQuery || loading) return
    void openConversation(conversationFromQuery).then(() => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          next.delete('conversation')
          return next
        },
        { replace: true },
      )
    })
  }, [conversationFromQuery, loading, openConversation, setSearchParams])

  const backToListPane = useCallback(() => {
    setMobilePane('list')
    setSelectedNoticeId(null)
    setSelectedRequest(null)
  }, [])

  const openNoticeDetail = useCallback((notice: any) => {
    setSelectedRequest(null)
    setSelectedNoticeId(notice.id)
    setMobilePane('chat')
    if (!notice.is_read) {
      void imApi.readNotifications([notice.id]).then(() => {
        setNotices((prev) =>
          prev.map((n) => (n.id === notice.id ? { ...n, is_read: true } : n)),
        )
      })
    }
  }, [])

  const openFriendRequestDetail = useCallback((req: any) => {
    setSelectedNoticeId(null)
    setSelectedRequest({ kind: 'friend', data: req })
    setMobilePane('chat')
  }, [])

  const openGroupRequestDetail = useCallback((req: any) => {
    setSelectedNoticeId(null)
    setSelectedRequest({ kind: 'group', data: req })
    setMobilePane('chat')
  }, [])

  useEffect(() => {
    activeIdRef.current = activeId
  }, [activeId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeId])

  const appendIncomingMessage = useCallback((raw: any) => {
    const convId = raw.conversation_id
    if (!convId) return
    const viewing = convId === activeIdRef.current
    if (viewing) {
      setMessages((prev) => {
        if (prev.some((m) => m.id === raw.id)) return prev
        return [...prev, raw]
      })
      void imApi.markConversationRead({ id: convId })
    }
    const preview = messagePreviewText(raw)
    setConversations((prev) => {
      const hit = prev.some((c) => c.id === convId)
      if (!hit) return prev
      return sortConversations(
        prev.map((c) =>
          c.id === convId
            ? {
                ...c,
                last_message_id: raw.id,
                last_message_at: raw.created_at,
                last_message: preview,
                unread_count: viewing ? 0 : (c.unread_count || 0) + 1,
              }
            : c,
        ),
      )
    })
  }, [])

  useImWebSocket(Boolean(isLogin()), {
    onNewMessage: (data) => {
      const convId = data?.conversation_id as string | undefined
      if (!convId) return
      appendIncomingMessage(data as any)
      // 会话可能尚不在列表中，轻量刷新列表；不覆盖当前消息区
      void reloadLists()
    },
    onOfflineMessages: (items) => {
      let touched = false
      for (const item of items) {
        const msg = unwrapOfflineMessage(item)
        if (!msg) continue
        touched = true
        appendIncomingMessage(msg)
      }
      if (touched) void reloadLists()
    },
    onNewNotification: (data) => {
      if (!data?.id) return
      setNotices((prev) => {
        if (prev.some((n) => n.id === data.id)) return prev
        return [
          {
            ...data,
            is_read: data.is_read ?? false,
            severity: String(data.severity || 'INFO').toLowerCase(),
          } as any,
          ...prev,
        ]
      })
    },
    onNewFriendRequest: () => {
      void reloadLists()
    },
    onNewJoinRequest: () => {
      void reloadLists()
    },
    onJoinRequestHandled: () => {
      void reloadLists()
    },
  })

  function onPickFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (!files.length) return
    setPendingFiles((prev) => [
      ...prev,
      ...files.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
        file,
      })),
    ])
    event.target.value = ''
  }

  async function send() {
    const text = draft.trim()
    if (!activeId || sending) return
    if (!text && !pendingFiles.length) return
    setSending(true)
    try {
      const attachments: any[] = []
      for (const item of pendingFiles) {
        const res = await fileApi.uploadFile(item.file)
        const data = res.data
        if (!data?.id) {
          throw new Error(`upload failed: ${item.name}`)
        }
        attachments.push({
          file_id: data.id,
          name: data.original_name || item.name,
          url: data.url || data.id,
          size: data.size ?? item.size,
          content_type: data.content_type || item.type,
        })
      }
      const res = await imApi.sendMessage({
        conversation_id: activeId,
        content: text || ' ',
        content_type: attachments.length ? 'file' : 'text',
        msg_type: attachments.length ? 'FILE' : 'TEXT',
        attachments: attachments.length ? attachments : undefined,
      })
      setDraft('')
      setPendingFiles([])
      if (res.data) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === res.data.id)) return prev
          return [...prev, res.data]
        })
        const preview = messagePreviewText(res.data)
        setConversations((prev) =>
          sortConversations(
            prev.map((c) =>
              c.id === activeId
                ? {
                    ...c,
                    last_message_id: res.data.id,
                    last_message_at: res.data.created_at,
                    last_message: preview,
                  }
                : c,
            ),
          ),
        )
      }
      await reloadLists()
    } catch {
      message.error('发送失败')
    } finally {
      setSending(false)
    }
  }

  async function startChatWithFriend(friend: any) {
    try {
      const res = await imApi.createDirect({
        account_type: friend.friend_account_type,
        account_id: friend.friend_account_id,
      })
      await reloadLists()
      const id = res.data?.id
      if (id) await openConversation(id)
    } catch {
      message.error('打开会话失败')
    }
  }

  async function doSearch() {
    const kw = searchKw.trim()
    if (!kw) return
    setSearching(true)
    try {
      if (addMode === 'friend') {
        const res = await imApi.searchUsers(kw)
        setSearchHits(res.data ?? [])
        setGroupHits([])
      } else {
        const res = await imApi.searchGroups(kw)
        setGroupHits(res.data ?? [])
        setSearchHits([])
      }
    } catch {
      message.error('搜索失败')
    } finally {
      setSearching(false)
    }
  }

  async function applyFriend(user: any) {
    if (user.is_friend || user.has_pending_request) return
    const key = `${user.account_type}:${user.account_id}`
    setSearchHits((prev) =>
      prev.map((u) =>
        `${u.account_type}:${u.account_id}` === key ? { ...u, has_pending_request: true } : u,
      ),
    )
    try {
      await imApi.applyFriend({
        applicant_type: myType,
        applicant_id: myId,
        recipient_type: user.account_type,
        recipient_id: user.account_id,
        message: '你好，交个朋友',
      })
      message.success('已发送好友申请')
    } catch {
      setSearchHits((prev) =>
        prev.map((u) =>
          `${u.account_type}:${u.account_id}` === key ? { ...u, has_pending_request: false } : u,
        ),
      )
      message.error('申请失败')
    }
  }

  async function applyJoinGroup(group: any) {
    if (group.is_member || group.has_pending_request) return
    setGroupHits((prev) =>
      prev.map((g) => (g.id === group.id ? { ...g, has_pending_request: true } : g)),
    )
    try {
      await imApi.applyJoinGroup({ group_id: group.id, message: '申请加入群聊' })
      message.success('已发送入群申请')
    } catch {
      setGroupHits((prev) =>
        prev.map((g) => (g.id === group.id ? { ...g, has_pending_request: false } : g)),
      )
      message.error('申请失败')
    }
  }

  async function handleFriendRequestAction(id: string, action: 'ACCEPT' | 'REJECT') {
    const req = requests.find((r) => r.id === id)
    if (!req || !isIncomingFriend(req)) {
      message.warning('只能处理发给自己的好友申请')
      return
    }
    try {
      await imApi.handleFriendRequest({ request_id: id, action })
      message.success(action === 'ACCEPT' ? '已同意' : '已拒绝')
      const nextStatus = action === 'ACCEPT' ? 'ACCEPTED' : 'REJECTED'
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: nextStatus } : r)),
      )
      setSelectedRequest((prev) =>
        prev?.kind === 'friend' && prev.data.id === id
          ? { kind: 'friend', data: { ...prev.data, status: nextStatus } }
          : prev,
      )
      await reloadLists()
    } catch {
      message.error('处理失败')
    }
  }

  async function handleJoinRequestAction(id: string, status: 'ACCEPTED' | 'REJECTED') {
    if (!pendingJoinRequests.some((r) => r.id === id)) {
      message.warning('只能处理待审批的入群申请')
      return
    }
    try {
      await imApi.handleJoinGroupRequest({ id, status })
      message.success(status === 'ACCEPTED' ? '已通过' : '已拒绝')
      setPendingJoinRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status } : r)),
      )
      setMyJoinRequests((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)))
      setSelectedRequest((prev) =>
        prev?.kind === 'group' && prev.data.id === id
          ? { kind: 'group', data: { ...prev.data, status } }
          : prev,
      )
      await reloadLists()
    } catch {
      message.error('处理失败')
    }
  }

  function friendRequestTitle(req: any) {
    if (isIncomingFriend(req)) return req.applicant_name || '好友申请'
    return req.recipient_name || '好友申请'
  }

  function friendRequestHint(req: any) {
    if (req.status !== 'PENDING') return req.message || '-'
    if (isIncomingFriend(req)) return req.message || '请求添加你为好友'
    return '等待对方处理'
  }

  function noticeSeverityTone(severity: string) {
    const s = severity.toLowerCase()
    if (s === 'error') return 'var(--ant-color-error)'
    if (s === 'warning') return 'var(--ant-color-warning)'
    return 'var(--ant-color-primary)'
  }

  async function createGroup() {
    if (!groupName.trim() || creatingGroup) return
    setCreatingGroup(true)
    try {
      const res = await imApi.createGroup({
        name: groupName.trim(),
        description: groupDesc.trim() || undefined,
      })
      const group = res.data
      const members = groupInvitees
        .map((fid) => friends.find((f) => f.friendship_id === fid))
        .filter(Boolean)
        .map((f) => ({
          account_type: f!.friend_account_type,
          account_id: f!.friend_account_id,
        }))
      if (group?.id && members.length) {
        await imApi.addGroupMembers({ group_id: group.id, members })
      }
      message.success('群聊已创建')
      setCreateGroupOpen(false)
      setGroupName('')
      setGroupDesc('')
      setGroupInvitees([])
      await reloadLists()
      const convRes = await imApi.conversationList({ current: 1, size: 50 })
      const list = convRes.data.records ?? []
      setConversations(list)
      const found = list.find((c: any) => c.group_id === group?.id)
      if (found) await openConversation(found.id)
    } catch {
      message.error('创建群聊失败')
    } finally {
      setCreatingGroup(false)
    }
  }

  async function openGroupManage(group: any) {
    setGroupManageId(group.id)
    try {
      const res = await imApi.groupMemberList(group.id)
      setGroupMembers(res.data ?? [])
    } catch {
      setGroupMembers([])
    }
  }

  const manageGroup = groups.find((g) => g.id === groupManageId) || null
  const isOwner =
    manageGroup &&
    manageGroup.owner_account_type === myType &&
    manageGroup.owner_account_id === myId

  async function dissolveCurrentGroup() {
    if (!manageGroup) return
    try {
      await imApi.dissolveGroup({ id: manageGroup.id })
      message.success('已解散')
      setGroupManageId(null)
      if (active?.group_id === manageGroup.id) {
        setActiveId(null)
        setMessages([])
        setMobilePane('list')
      }
      await reloadLists()
    } catch {
      message.error('解散失败')
    }
  }

  async function setMemberRole(member: any, role: string) {
    if (!manageGroup) return
    try {
      await imApi.setGroupMemberRole({
        group_id: manageGroup.id,
        account_type: member.account_type,
        account_id: member.account_id,
        role,
      })
      setGroupMembers((prev) =>
        prev.map((m) =>
          m.account_type === member.account_type && m.account_id === member.account_id
            ? { ...m, role }
            : m,
        ),
      )
      message.success('已更新角色')
    } catch {
      message.error('设置失败')
    }
  }

  if (!isLogin()) {
    return (
      <div className="page-shell py-20">
        <Empty description="请登录后使用消息" />
      </div>
    )
  }

  const showListPane = !isMobile || mobilePane === 'list'
  const showChatPane = !isMobile || mobilePane === 'chat'
  const sidebarBtn = (active: boolean) =>
    `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
      active
        ? 'bg-[var(--ant-color-primary)] text-white'
        : 'text-white/75 hover:bg-white/10 hover:text-white'
    }`

  return (
    <div className="page-shell flex h-[calc(100dvh-64px)] flex-col md:h-[calc(100vh-64px)] md:px-4 md:py-4">
      <div
        className={`panel grid min-h-0 flex-1 overflow-hidden rounded-none md:grid-cols-[60px_300px_minmax(0,1fr)] md:rounded-xl ${
          isMobile ? 'grid-cols-1' : ''
        }`}
      >
        {/* Admin 式左侧图标栏（桌面） */}
        <aside className="hidden h-full min-h-0 flex-col items-center bg-[#2b2b2b] py-3 md:flex">
          <Tooltip title="个人中心" placement="right">
            <button
              type="button"
              className="shrink-0"
              onClick={() => navigate('/profile')}
              aria-label="个人中心"
            >
              <Avatar size={40} src={myAvatar || undefined}>
                {myName.charAt(0)}
              </Avatar>
            </button>
          </Tooltip>
          <div className="mt-6 flex flex-col items-center gap-5">
            <Tooltip title="聊天" placement="right">
              <Badge count={totalUnreadCount} overflowCount={99} offset={[-2, 2]}>
                <button
                  type="button"
                  className={sidebarBtn(activeSection === 'chat')}
                  aria-label="聊天"
                  onClick={() => openSection('chat')}
                >
                  <MessageOutlined className="text-xl" />
                </button>
              </Badge>
            </Tooltip>
            <Tooltip title="通讯录" placement="right">
              <button
                type="button"
                className={sidebarBtn(activeSection === 'contacts')}
                aria-label="通讯录"
                onClick={() => openSection('contacts')}
              >
                <TeamOutlined className="text-xl" />
              </button>
            </Tooltip>
            <Tooltip title="通知" placement="right">
              <Badge count={noticeBadgeTotal} overflowCount={99} offset={[-2, 2]}>
                <button
                  type="button"
                  className={sidebarBtn(activeSection === 'notice')}
                  aria-label="通知"
                  onClick={() => openSection('notice')}
                >
                  <BellOutlined className="text-xl" />
                </button>
              </Badge>
            </Tooltip>
          </div>
        </aside>

        {/* 列表区 */}
        <aside
          className={`min-h-0 flex-col border-[var(--ant-color-border)] md:border-r ${
            showListPane ? 'flex' : 'hidden'
          } ${isMobile ? 'h-full' : ''}`}
        >
          {activeSection === 'chat' || activeSection === 'contacts' ? (
            <div className="flex items-center justify-between gap-2 border-b border-[var(--ant-color-border)] px-3 py-3">
              {activeSection === 'contacts' ? (
                <Segmented
                  value={contactTab}
                  onChange={(v) => setContactTab(v as 'friends' | 'groups')}
                  options={[
                    { label: '好友', value: 'friends' },
                    { label: '群组', value: 'groups' },
                  ]}
                />
              ) : (
                <div className="text-sm font-semibold">聊天</div>
              )}
              <Dropdown
                menu={{ items: contactAddMenu }}
                trigger={['click']}
                placement="bottomRight"
              >
                <Button type="text" icon={<PlusOutlined />} aria-label="更多操作" />
              </Dropdown>
            </div>
          ) : null}

          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <Spin
              spinning={loading}
              className="flex min-h-0 flex-1 flex-col [&_.ant-spin-container]:flex [&_.ant-spin-container]:min-h-0 [&_.ant-spin-container]:flex-1 [&_.ant-spin-container]:flex-col"
            >
              {activeSection === 'chat' ? (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  {sortedConversations.length ? (
                    sortedConversations.map((c) => (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => void openConversation(c.id)}
                        className={`flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-[var(--ant-color-fill-quaternary)] ${
                          activeId === c.id ? 'bg-[var(--ant-color-fill-secondary)]' : ''
                        }`}
                      >
                        <Badge count={c.unread_count || 0} overflowCount={99}>
                          <Avatar size={40} src={resolveFileUrl(c.avatar) || undefined}>
                            {(c.title || '?').charAt(0)}
                          </Avatar>
                        </Badge>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-3">
                            <span className="min-w-0 flex-1 truncate text-sm font-semibold">
                              {c.title || '会话'}
                            </span>
                            <span className="muted-text shrink-0 text-xs">
                              {formatDateTime(c.last_message_at ?? c.created_at)}
                            </span>
                          </div>
                          <div className="muted-text mt-1 truncate text-xs">
                            {conversationPreview(c, { activeId, messages })}
                          </div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <Empty className="py-12" description="暂无会话" />
                  )}
                </div>
              ) : null}

              {activeSection === 'contacts' && contactTab === 'friends' ? (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  {friends.length ? (
                    friends.map((f) => {
                      const name = friendListName(f)
                      return (
                        <button
                          key={f.friendship_id}
                          type="button"
                          onClick={() => void startChatWithFriend(f)}
                          className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-[var(--ant-color-fill-quaternary)]"
                        >
                          <Avatar size={40} src={resolveFileUrl(f.avatar) || undefined}>
                            {name.charAt(0)}
                          </Avatar>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-3">
                              <span className="min-w-0 flex-1 truncate text-sm font-semibold">
                                {name}
                              </span>
                              <Tag className="m-0 shrink-0">{typeLabel(f.friend_account_type)}</Tag>
                            </div>
                            <div className="muted-text mt-1 truncate text-xs">
                              {f.signature || '-'}
                            </div>
                          </div>
                        </button>
                      )
                    })
                  ) : (
                    <Empty className="py-12" description="暂无好友" />
                  )}
                </div>
              ) : null}

              {activeSection === 'contacts' && contactTab === 'groups' ? (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  {groups.length ? (
                    groups.map((g) => (
                      <div
                        key={g.id}
                        className="flex items-start gap-3 px-4 py-3 hover:bg-[var(--ant-color-fill-quaternary)]"
                      >
                        <Avatar size={40} src={resolveFileUrl(g.avatar) || undefined}>
                          {(g.name || '?').charAt(0)}
                        </Avatar>
                        <button
                          type="button"
                          className="min-w-0 flex-1 text-left"
                          onClick={() => {
                            const conv = conversations.find((c) => c.group_id === g.id)
                            if (conv) void openConversation(conv.id)
                            else message.info('暂无会话，请从好友建群后进入')
                          }}
                        >
                          <div className="truncate text-sm font-semibold">{g.name}</div>
                          <div className="muted-text mt-1 truncate text-xs">
                            {g.member_count} 人 · {g.description || '-'}
                          </div>
                        </button>
                        <Button type="link" onClick={() => void openGroupManage(g)}>
                          管理
                        </Button>
                      </div>
                    ))
                  ) : (
                    <Empty className="py-12" description="暂无群组" />
                  )}
                </div>
              ) : null}

              {activeSection === 'notice' ? (
                <div className="flex min-h-0 flex-1 flex-col">
                  <div className="border-b border-[var(--ant-color-border)] px-3 py-2">
                    <Segmented
                      block
                      value={noticeTab}
                      onChange={(v) => setNoticeTab(v as 'notices' | 'requests')}
                      options={[
                        {
                          label: unreadNoticeCount
                            ? `通知 (${unreadNoticeCount})`
                            : '通知',
                          value: 'notices',
                        },
                        {
                          label: incomingPendingCount
                            ? `申请 (${incomingPendingCount})`
                            : '申请',
                          value: 'requests',
                        },
                      ]}
                    />
                  </div>
                  <div className="min-h-0 flex-1 overflow-y-auto">
                    {noticeTab === 'notices' ? (
                      notices.length ? (
                        notices.map((n) => (
                          <button
                            key={n.id}
                            type="button"
                            onClick={() => openNoticeDetail(n)}
                            className={`flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-[var(--ant-color-fill-quaternary)] ${
                              selectedNoticeId === n.id
                                ? 'bg-[var(--ant-color-fill-secondary)]'
                                : ''
                            }`}
                          >
                            <Avatar
                              size={40}
                              style={{ backgroundColor: noticeSeverityTone(n.severity) }}
                            >
                              {n.severity === 'error' || n.severity === 'warning' ? '!' : 'i'}
                            </Avatar>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex min-w-0 items-center gap-2">
                                  <span
                                    className={`truncate text-sm ${
                                      n.is_read ? '' : 'font-bold'
                                    }`}
                                  >
                                    {n.title}
                                  </span>
                                  {!n.is_read ? (
                                    <Tag color="blue" className="m-0 shrink-0">
                                      新
                                    </Tag>
                                  ) : null}
                                </div>
                                <span className="muted-text shrink-0 text-xs">
                                  {formatDateTime(n.created_at)}
                                </span>
                              </div>
                              <div className="muted-text mt-1 truncate text-xs">{n.content}</div>
                            </div>
                          </button>
                        ))
                      ) : (
                        <Empty className="py-12" description="暂无通知" />
                      )
                    ) : null}

                    {noticeTab === 'requests' ? (
                      requests.length || combinedGroupJoinRequests.length ? (
                        <>
                          {requests.map((req) => {
                            const title = friendRequestTitle(req)
                            const avatar = isIncomingFriend(req)
                              ? req.applicant_avatar
                              : req.recipient_avatar
                            return (
                              <button
                                key={`f-${req.id}`}
                                type="button"
                                onClick={() => openFriendRequestDetail(req)}
                                className={`relative flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-[var(--ant-color-fill-quaternary)] ${
                                  selectedRequest?.kind === 'friend' &&
                                  selectedRequest.data.id === req.id
                                    ? 'bg-[var(--ant-color-fill-secondary)]'
                                    : ''
                                }`}
                              >
                                {req.status !== 'PENDING' ? (
                                  <span
                                    className={`pointer-events-none absolute bottom-2 right-2 z-10 rotate-[-15deg] rounded border-2 bg-white px-2 text-[11px] font-bold opacity-70 ${
                                      req.status === 'ACCEPTED'
                                        ? 'border-green-600 text-green-600'
                                        : 'border-red-500 text-red-500'
                                    }`}
                                  >
                                    {req.status === 'ACCEPTED' ? '已通过' : '已拒绝'}
                                  </span>
                                ) : null}
                                <Avatar size={40} src={resolveFileUrl(avatar) || undefined}>
                                  {title.charAt(0)}
                                </Avatar>
                                <div className="min-w-0 flex-1">
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex min-w-0 items-center gap-2">
                                      <span className="truncate text-sm font-bold">{title}</span>
                                      {req.status === 'PENDING' && !isIncomingFriend(req) ? (
                                        <Tag className="m-0 shrink-0">已申请</Tag>
                                      ) : null}
                                    </div>
                                    <span className="muted-text shrink-0 text-xs">
                                      {formatDateTime(req.created_at)}
                                    </span>
                                  </div>
                                  <div className="muted-text mt-1 truncate text-xs">
                                    {friendRequestHint(req)}
                                  </div>
                                </div>
                              </button>
                            )
                          })}
                          {combinedGroupJoinRequests.map((req) => (
                            <button
                              key={`g-${req.id}`}
                              type="button"
                              onClick={() => openGroupRequestDetail(req)}
                              className={`relative flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-[var(--ant-color-fill-quaternary)] ${
                                selectedRequest?.kind === 'group' &&
                                selectedRequest.data.id === req.id
                                  ? 'bg-[var(--ant-color-fill-secondary)]'
                                  : ''
                              }`}
                            >
                              {req.status !== 'PENDING' ? (
                                <span
                                  className={`pointer-events-none absolute bottom-2 right-2 z-10 rotate-[-15deg] rounded border-2 bg-white px-2 text-[11px] font-bold opacity-70 ${
                                    req.status === 'ACCEPTED'
                                      ? 'border-green-600 text-green-600'
                                      : 'border-red-500 text-red-500'
                                  }`}
                                >
                                  {req.status === 'ACCEPTED' ? '已通过' : '已拒绝'}
                                </span>
                              ) : null}
                              <Avatar
                                size={40}
                                src={resolveFileUrl(req.applicant_avatar) || undefined}
                              >
                                {(req.applicant_name || '?').charAt(0)}
                              </Avatar>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-start justify-between gap-3">
                                  <span className="truncate text-sm font-bold">
                                    {req.group_name || req.applicant_name || '入群申请'}
                                  </span>
                                  <span className="muted-text shrink-0 text-xs">
                                    {formatDateTime(req.created_at)}
                                  </span>
                                </div>
                                <div className="muted-text mt-1 truncate text-xs">
                                  {req.message || req.group_name || '-'}
                                </div>
                              </div>
                            </button>
                          ))}
                        </>
                      ) : (
                        <Empty className="py-12" description="暂无待处理申请" />
                      )
                    ) : null}
                  </div>
                </div>
              ) : null}
            </Spin>
          </div>
        </aside>

        <section
          className={`min-h-0 min-w-0 flex-col ${showChatPane ? 'flex' : 'hidden'} ${
            isMobile ? 'h-full' : ''
          }`}
        >
          {selectedNotice ? (
            <div className="flex h-full min-h-0 flex-col overflow-y-auto px-4 py-6">
              {isMobile ? (
                <div className="mb-3">
                  <Button type="text" icon={<ArrowLeftOutlined />} onClick={backToListPane}>
                    返回
                  </Button>
                </div>
              ) : null}
              <div className="mx-auto flex w-full max-w-[460px] flex-col gap-4">
                <div className="flex items-center gap-3">
                  <Avatar
                    size={64}
                    style={{ backgroundColor: noticeSeverityTone(selectedNotice.severity) }}
                  >
                    {selectedNotice.severity === 'error' || selectedNotice.severity === 'warning'
                      ? '!'
                      : 'i'}
                  </Avatar>
                  <div className="min-w-0">
                    <div className="truncate text-lg font-semibold">{selectedNotice.title}</div>
                    <div className="muted-text text-xs">
                      {formatDateTime(selectedNotice.created_at)}
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--ant-color-border)] bg-[var(--ant-color-bg-container)] px-4 py-4 text-sm leading-7 whitespace-pre-wrap">
                  {selectedNotice.content}
                </div>
                <div className="flex justify-center">
                  <Button
                    onClick={() => {
                      setSelectedNoticeId(null)
                      if (isMobile) backToListPane()
                    }}
                  >
                    关闭
                  </Button>
                </div>
              </div>
            </div>
          ) : selectedRequest ? (
            <div className="flex h-full min-h-0 flex-col overflow-y-auto px-4 py-6">
              {isMobile ? (
                <div className="mb-3">
                  <Button type="text" icon={<ArrowLeftOutlined />} onClick={backToListPane}>
                    返回
                  </Button>
                </div>
              ) : null}
              <div className="mx-auto flex w-full max-w-[460px] flex-col gap-4">
                <div className="relative flex items-center gap-3 overflow-visible">
                  <Avatar
                    size={64}
                    src={
                      resolveFileUrl(
                        selectedRequest.kind === 'friend'
                          ? isIncomingFriend(selectedRequest.data)
                            ? selectedRequest.data.applicant_avatar
                            : selectedRequest.data.recipient_avatar
                          : selectedRequest.data.applicant_avatar,
                      ) || undefined
                    }
                  >
                    {(selectedRequest.kind === 'friend'
                      ? friendRequestTitle(selectedRequest.data)
                      : selectedRequest.data.applicant_name || '?'
                    ).charAt(0)}
                  </Avatar>
                  <div className="min-w-0">
                    <div className="truncate text-lg font-semibold">
                      {selectedRequest.kind === 'friend'
                        ? friendRequestTitle(selectedRequest.data)
                        : selectedRequest.data.applicant_name || '入群申请'}
                    </div>
                    <div className="muted-text text-xs">
                      {selectedRequest.kind === 'group'
                        ? selectedRequest.data.group_name || '入群申请'
                        : '好友申请'}
                    </div>
                  </div>
                  {selectedRequest.data.status !== 'PENDING' ? (
                    <span
                      className={`pointer-events-none absolute bottom-0 right-0 rotate-[-15deg] rounded border-2 bg-white px-2 text-[11px] font-bold opacity-70 ${
                        selectedRequest.data.status === 'ACCEPTED'
                          ? 'border-green-600 text-green-600'
                          : 'border-red-500 text-red-500'
                      }`}
                    >
                      {selectedRequest.data.status === 'ACCEPTED' ? '已通过' : '已拒绝'}
                    </span>
                  ) : null}
                </div>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="muted-text">类型：</span>
                    {selectedRequest.kind === 'group' ? '入群申请' : '好友申请'}
                  </div>
                  <div>
                    <span className="muted-text">说明：</span>
                    {selectedRequest.data.message || '-'}
                  </div>
                  <div>
                    <span className="muted-text">时间：</span>
                    {formatDateTime(selectedRequest.data.created_at)}
                  </div>
                </div>
                <div className="flex flex-wrap justify-center gap-3">
                  {canHandleSelectedRequest ? (
                    <>
                      <Button
                        type="primary"
                        onClick={() => {
                          if (selectedRequest.kind === 'friend') {
                            void handleFriendRequestAction(selectedRequest.data.id, 'ACCEPT')
                          } else {
                            void handleJoinRequestAction(selectedRequest.data.id, 'ACCEPTED')
                          }
                        }}
                      >
                        通过
                      </Button>
                      <Button
                        danger
                        onClick={() => {
                          if (selectedRequest.kind === 'friend') {
                            void handleFriendRequestAction(selectedRequest.data.id, 'REJECT')
                          } else {
                            void handleJoinRequestAction(selectedRequest.data.id, 'REJECTED')
                          }
                        }}
                      >
                        拒绝
                      </Button>
                    </>
                  ) : (
                    <Tag>
                      {selectedRequest.data.status === 'ACCEPTED'
                        ? '已通过'
                        : selectedRequest.data.status === 'REJECTED'
                          ? '已拒绝'
                          : '等待对方处理'}
                    </Tag>
                  )}
                </div>
              </div>
            </div>
          ) : active ? (
            <>
              <div className="flex items-center gap-2 border-b border-[var(--ant-color-border)] px-3 py-3 md:gap-3 md:px-4">
                {isMobile ? (
                  <Button
                    type="text"
                    icon={<ArrowLeftOutlined />}
                    aria-label="返回会话列表"
                    onClick={backToListPane}
                  />
                ) : null}
                <Avatar
                  size={isMobile ? 36 : 42}
                  src={resolveFileUrl(active.avatar) || undefined}
                  icon={
                    active.conversation_type === 'GROUP' ? <TeamOutlined /> : <UserOutlined />
                  }
                />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold">
                    {active.title || (active.conversation_type === 'GROUP' ? '群聊' : '私聊')}
                  </div>
                  <div className="muted-text text-xs">
                    {active.conversation_type === 'GROUP' ? '群聊' : '私聊'}
                  </div>
                </div>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3 md:px-4 md:py-4">
                <Spin spinning={msgLoading}>
                  <Image.PreviewGroup>
                    <div className="flex flex-col gap-3">
                      {messages.map((m) => {
                        const mine =
                          m.sender_account_type === myType && m.sender_account_id === myId
                        const senderLabel =
                          m.sender_nickname || m.sender_name || m.sender_account_id || '未知'
                        const avatarLetter = (senderLabel || '?').charAt(0)
                        return (
                          <div
                            key={m.id}
                            className={`flex items-start gap-2 ${mine ? 'flex-row-reverse' : ''}`}
                          >
                            <Avatar
                              size={28}
                              className="shrink-0"
                              src={resolveFileUrl(m.sender_avatar) || undefined}
                            >
                              {avatarLetter}
                            </Avatar>
                            <div className="min-w-0 max-w-[min(78%,640px)] md:max-w-[min(68%,640px)]">
                              <div
                                className={`mb-1 flex gap-2 text-xs muted-text ${
                                  mine ? 'justify-end' : 'justify-start'
                                }`}
                              >
                                <span>
                                  {senderLabel}
                                  {m.sender_account_type ? (
                                    <span className="opacity-70">
                                      {' '}
                                      · {typeLabel(m.sender_account_type)}
                                    </span>
                                  ) : null}
                                </span>
                                <span>{formatDateTime(m.created_at)}</span>
                              </div>
                              <div
                                className={`rounded-lg px-3 py-2 text-sm leading-6 ${
                                  mine
                                    ? 'bg-[var(--ant-color-primary)] text-white'
                                    : 'border border-[var(--ant-color-border)] bg-[var(--ant-color-bg-container)]'
                                }`}
                              >
                                {m.is_revoked ? (
                                  <div className="italic opacity-60">消息已撤回</div>
                                ) : (
                                  <>
                                    {m.content?.trim() ? (
                                      <div className="whitespace-pre-wrap break-words">
                                        {m.content}
                                      </div>
                                    ) : null}
                                    {m.attachments?.length ? (
                                      <div className="mt-2 flex flex-col gap-2">
                                        {m.attachments.map((att: any, idx: any) => {
                                          const url = resolveFileUrl(att.url)
                                          const key = att.file_id || `${att.name}-${idx}`
                                          if (isImageFile(att) && url) {
                                            return (
                                              <Image
                                                key={key}
                                                src={url}
                                                alt={att.name}
                                                className="max-h-40 max-w-full rounded object-cover"
                                                style={{ maxHeight: 160 }}
                                                rootClassName="!block"
                                              />
                                            )
                                          }
                                          return (
                                            <a
                                              key={key}
                                              href={url}
                                              target="_blank"
                                              rel="noreferrer"
                                              className={`flex items-center gap-2 rounded px-2 py-1.5 text-xs ${
                                                mine
                                                  ? 'bg-white/15 hover:bg-white/25'
                                                  : 'bg-[var(--ant-color-fill-secondary)] hover:bg-[var(--ant-color-fill)]'
                                              }`}
                                            >
                                              <PaperClipOutlined />
                                              <span className="min-w-0 flex-1 truncate font-medium">
                                                {att.name}
                                              </span>
                                              <span className="shrink-0 opacity-70">
                                                {formatFileSize(att.size)}
                                              </span>
                                            </a>
                                          )
                                        })}
                                      </div>
                                    ) : null}
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                      <div ref={bottomRef} />
                    </div>
                  </Image.PreviewGroup>
                </Spin>
              </div>
              <div className="border-t border-[var(--ant-color-border)] p-3">
                {pendingFiles.length ? (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {pendingFiles.map((f, index) => (
                      <Tag
                        key={`${f.name}-${index}`}
                        closable
                        onClose={() =>
                          setPendingFiles((prev) => prev.filter((_, i) => i !== index))
                        }
                        icon={<PaperClipOutlined />}
                      >
                        {f.name}
                      </Tag>
                    ))}
                  </div>
                ) : null}
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={onPickFiles}
                  />
                  <Button
                    icon={<PaperClipOutlined />}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={sending}
                  />
                  <Input.TextArea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    autoSize={{ minRows: 1, maxRows: 4 }}
                    placeholder="输入消息或添加附件，Enter 发送"
                    onPressEnter={(e) => {
                      if (!e.shiftKey) {
                        e.preventDefault()
                        void send()
                      }
                    }}
                  />
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={sending}
                    disabled={!draft.trim() && !pendingFiles.length}
                    onClick={() => void send()}
                  >
                    发送
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4">
              {isMobile ? (
                <Button type="text" icon={<ArrowLeftOutlined />} onClick={backToListPane}>
                  返回列表
                </Button>
              ) : null}
              <Empty
                description={
                  activeSection === 'notice'
                    ? '选择通知或申请查看详情'
                    : '选择会话或好友开始聊天'
                }
              />
            </div>
          )}
        </section>
      </div>

      {/* 移动端底部导航（对齐 Admin MobileBottomNav） */}
      {isMobile ? (
        <nav className="flex shrink-0 items-center justify-around border-t border-[var(--ant-color-border)] bg-[var(--ant-color-bg-container)] py-1">
          <button
            type="button"
            className={`flex flex-col items-center gap-0.5 px-3 py-1 ${
              activeSection === 'chat'
                ? 'text-[var(--ant-color-primary)]'
                : 'text-[var(--ant-color-text-tertiary)]'
            }`}
            onClick={() => openSection('chat')}
          >
            <Badge count={totalUnreadCount} overflowCount={99} offset={[4, -2]}>
              <MessageOutlined className="text-xl" />
            </Badge>
            <span className="text-[10px] leading-none">聊天</span>
          </button>
          <button
            type="button"
            className={`flex flex-col items-center gap-0.5 px-3 py-1 ${
              activeSection === 'contacts'
                ? 'text-[var(--ant-color-primary)]'
                : 'text-[var(--ant-color-text-tertiary)]'
            }`}
            onClick={() => openSection('contacts')}
          >
            <TeamOutlined className="text-xl" />
            <span className="text-[10px] leading-none">通讯录</span>
          </button>
          <button
            type="button"
            className={`flex flex-col items-center gap-0.5 px-3 py-1 ${
              activeSection === 'notice'
                ? 'text-[var(--ant-color-primary)]'
                : 'text-[var(--ant-color-text-tertiary)]'
            }`}
            onClick={() => openSection('notice')}
          >
            <Badge count={noticeBadgeTotal} overflowCount={99} offset={[4, -2]}>
              <BellOutlined className="text-xl" />
            </Badge>
            <span className="text-[10px] leading-none">通知</span>
          </button>
        </nav>
      ) : null}

      <Modal
        title="添加好友 / 群聊"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        footer={null}
        destroyOnHidden
      >
        <Segmented
          block
          className="mb-3"
          value={addMode}
          onChange={(v) => {
            setAddMode(v as 'friend' | 'group')
            setSearchHits([])
            setGroupHits([])
            setSearchKw('')
          }}
          options={[
            { label: '添加好友', value: 'friend' },
            { label: '加入群聊', value: 'group' },
          ]}
        />
        <div className="flex gap-2">
          <Input
            value={searchKw}
            onChange={(e) => setSearchKw(e.target.value)}
            placeholder={
              addMode === 'friend' ? '搜索昵称 / 账号（跨端）' : '搜索群聊名称'
            }
            onPressEnter={() => void doSearch()}
          />
          <Button type="primary" loading={searching} onClick={() => void doSearch()}>
            搜索
          </Button>
        </div>
        <div className="mt-4 max-h-80 space-y-2 overflow-y-auto">
          {addMode === 'friend'
            ? searchHits.map((u) => (
                <div
                  key={`${u.account_type}:${u.account_id}`}
                  className="flex items-center gap-3 rounded-lg px-2 py-2"
                >
                  <Avatar src={resolveFileUrl(u.avatar) || undefined} icon={<UserOutlined />} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {displayName({
                        name: u.name,
                        nickname: u.nickname,
                        fallback: u.account || u.account_id,
                      })}
                      <Tag className="ml-2">{typeLabel(u.account_type)}</Tag>
                    </div>
                    <div className="muted-text truncate text-xs">
                      {u.signature || u.account || '-'}
                    </div>
                  </div>
                  {u.is_friend ? (
                    <Tag color="success">已是好友</Tag>
                  ) : u.has_pending_request ? (
                    <Tag>已申请</Tag>
                  ) : (
                    <Button type="primary" onClick={() => void applyFriend(u)}>
                      申请
                    </Button>
                  )}
                </div>
              ))
            : groupHits.map((g) => (
                <div key={g.id} className="flex items-center gap-3 rounded-lg px-2 py-2">
                  <Avatar src={resolveFileUrl(g.avatar) || undefined} icon={<TeamOutlined />} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{g.name}</div>
                    <div className="muted-text truncate text-xs">
                      {g.member_count} 人 · {g.description || '-'}
                    </div>
                  </div>
                  {g.is_member ? (
                    <Tag color="success">已加入</Tag>
                  ) : g.has_pending_request ? (
                    <Tag>已申请</Tag>
                  ) : (
                    <Button type="primary" onClick={() => void applyJoinGroup(g)}>
                      申请
                    </Button>
                  )}
                </div>
              ))}
          {!searching &&
          (addMode === 'friend' ? searchHits.length === 0 : groupHits.length === 0) ? (
            <Empty description="输入关键词搜索" />
          ) : null}
        </div>
      </Modal>

      <Modal
        title="创建群聊"
        open={createGroupOpen}
        onCancel={() => setCreateGroupOpen(false)}
        onOk={() => void createGroup()}
        confirmLoading={creatingGroup}
        okText="创建"
        destroyOnHidden
      >
        <div className="space-y-3">
          <Input value={groupName} onChange={(e) => setGroupName(e.target.value)} placeholder="群名称" />
          <Input.TextArea
            value={groupDesc}
            onChange={(e) => setGroupDesc(e.target.value)}
            placeholder="群简介（可选）"
            autoSize={{ minRows: 2, maxRows: 4 }}
          />
          <div>
            <div className="mb-2 text-sm text-[var(--ant-color-text-secondary)]">邀请好友（可跨端）</div>
            <Select
              mode="multiple"
              className="w-full"
              placeholder="选择好友"
              value={groupInvitees}
              onChange={setGroupInvitees}
              options={friends.map((f) => ({
                value: f.friendship_id,
                label: `${displayName({ name: f.name, nickname: f.nickname, remark: f.remark })}（${typeLabel(f.friend_account_type)}）`,
              }))}
            />
          </div>
        </div>
      </Modal>

      <Modal
        title={manageGroup ? `管理 · ${manageGroup.name}` : '群管理'}
        open={Boolean(groupManageId)}
        onCancel={() => setGroupManageId(null)}
        footer={
          isOwner ? (
            <Button danger onClick={() => void dissolveCurrentGroup()}>
              解散群聊
            </Button>
          ) : (
            <Button
              danger
              onClick={async () => {
                if (!manageGroup) return
                try {
                  await imApi.leaveGroup({ id: manageGroup.id })
                  message.success('已退群')
                  setGroupManageId(null)
                  await reloadLists()
                } catch {
                  message.error('退群失败')
                }
              }}
            >
              退出群聊
            </Button>
          )
        }
        destroyOnHidden
      >
        <div className="max-h-96 space-y-2 overflow-y-auto">
          {groupMembers.map((m) => (
            <div key={`${m.account_type}:${m.account_id}`} className="flex items-center gap-2">
              <Avatar src={resolveFileUrl(m.profile_avatar) || undefined} icon={<UserOutlined />} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm">
                  {m.profile_name || m.nickname || m.account_id}
                  <Tag className="ml-1">{typeLabel(m.account_type)}</Tag>
                  <Tag className="ml-1">{m.role === 'OWNER' ? '群主' : m.role === 'ADMIN' ? '管理员' : '成员'}</Tag>
                </div>
              </div>
              {isOwner && m.role !== 'OWNER' ? (
                <Space size={4}>
                  {m.role !== 'ADMIN' ? (
                    <Button onClick={() => void setMemberRole(m, 'ADMIN')}>设管</Button>
                  ) : (
                    <Button onClick={() => void setMemberRole(m, 'MEMBER')}>取消管</Button>
                  )}
                  <Button
                    danger
                    onClick={async () => {
                      try {
                        await imApi.removeGroupMember({
                          group_id: manageGroup!.id,
                          account_type: m.account_type,
                          account_id: m.account_id,
                        })
                        setGroupMembers((prev) =>
                          prev.filter(
                            (x) => !(x.account_type === m.account_type && x.account_id === m.account_id),
                          ),
                        )
                        message.success('已移除')
                      } catch {
                        message.error('移除失败')
                      }
                    }}
                  >
                    移除
                  </Button>
                </Space>
              ) : null}
            </div>
          ))}
        </div>
      </Modal>
    </div>
  )
}
