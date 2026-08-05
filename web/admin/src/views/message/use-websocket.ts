import { ref, onUnmounted, readonly, type Ref } from 'vue'

export type WsConnectionState = 'connecting' | 'connected' | 'disconnected'

export interface WsMessage {
  type: string
  data?: any
}

export interface WsHandlers {
  onNewMessage?: (data: any) => void
  onTyping?: (data: {
    conversation_id: string
    account_type: string
    account_id: string
    is_typing: boolean
  }) => void
  onOfflineMessages?: (messages: any[]) => void
  onNewNotification?: (data: any) => void
  onNewFriendRequest?: (data: any) => void
  onNewJoinRequest?: (data: any) => void
  onJoinRequestHandled?: (data: {
    request_id: string
    group_id: string
    group_name: string
    status: string
  }) => void
}

/* ---- module-level singleton state ---- */

const connectionState: Ref<WsConnectionState> = ref('disconnected')
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let reconnectAttempt = 0
let closed = false

const subscriberMap = new Map<symbol, WsHandlers>()
let subscriberCount = 0
let connectPromise: Promise<void> | null = null

/* ---- internal functions ---- */

function sendRaw(data: Record<string, any>) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data))
  }
}

function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = setInterval(() => {
    sendRaw({ type: 'ping' })
  }, 25000)
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function scheduleReconnect() {
  if (closed) return
  if (connectionState.value === 'connected' || connectionState.value === 'connecting') return
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000)
  reconnectAttempt++
  reconnectTimer = setTimeout(() => connect(), delay)
}

function handleMessage(msg: WsMessage) {
  // Dispatch to all registered handlers
  subscriberMap.forEach((handlers) => {
    switch (msg.type) {
      case 'pong':
        break
      case 'new_message':
        handlers.onNewMessage?.(msg.data)
        break
      case 'typing':
        handlers.onTyping?.(msg.data)
        break
      case 'new_notification':
        handlers.onNewNotification?.(msg.data)
        break
      case 'new_friend_request':
        handlers.onNewFriendRequest?.(msg.data)
        break
      case 'new_join_request':
        handlers.onNewJoinRequest?.(msg.data)
        break
      case 'join_request_handled':
        handlers.onJoinRequestHandled?.(msg.data)
        break
      case 'offline_messages':
        handlers.onOfflineMessages?.(msg.data?.messages ?? [])
        break
    }
  })
}

function connect() {
  // ── State recovery / guards ──
  if (closed && subscriberCount > 0) closed = false
  if (closed) return
  if (connectPromise) return connectPromise
  if (ws?.readyState === WebSocket.OPEN) return
  if (ws?.readyState === WebSocket.CONNECTING) return

  const token = localStorage.getItem('token')
  if (!token) {
    connectionState.value = 'disconnected'
    return
  }
  const baseURL = import.meta.env.VITE_API_URL || ''
  let url: string
  if (baseURL.startsWith('http')) {
    url = `${baseURL.replace(/^http/, 'ws')}/api/v1/admin/message/ws?token=${encodeURIComponent(token)}`
  } else {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    url = `${proto}//${window.location.host}/api/v1/admin/message/ws?token=${encodeURIComponent(token)}`
  }

  connectionState.value = 'connecting'

  connectPromise = new Promise<void>((resolve) => {
    ws = new WebSocket(url)

    ws.onopen = () => {
      connectionState.value = 'connected'
      reconnectAttempt = 0
      connectPromise = null
      startHeartbeat()
      sendRaw({ type: 'pull_offline' })
      resolve()
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = (event: CloseEvent) => {
      connectPromise = null
      connectionState.value = 'disconnected'
      stopHeartbeat()
      if (event.code === 4001 || event.code === 4000) {
        closed = true
        return
      }
      scheduleReconnect()
    }

    ws.onerror = () => {
      // error 后 close 可能不会触发 onclose，直接触发重连
      connectPromise = null
      try {
        ws?.close()
      } catch {
        /* ignore */
      }
      scheduleReconnect()
    }
  })

  return connectPromise
}

function disconnect() {
  closed = true
  stopHeartbeat()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  ws?.close()
  ws = null
  connectionState.value = 'disconnected'
  subscriberMap.clear()
  subscriberCount = 0
}

function sendTyping(conversationId: string, isTyping: boolean) {
  sendRaw({
    type: isTyping ? 'typing_start' : 'typing_end',
    data: { conversation_id: conversationId },
  })
}

function markConversationRead(conversationId: string, lastReadMessageId: string) {
  sendRaw({
    type: 'read_conversation',
    data: { conversation_id: conversationId, last_read_message_id: lastReadMessageId },
  })
}

/* ---- public composable ---- */

export function useWebSocket(handlers: WsHandlers) {
  const key = Symbol()
  // 对象引用保持最新闭包，避免 setup 内 handlers 过期
  const live = handlers
  const proxy: WsHandlers = {
    onNewMessage: (d) => live.onNewMessage?.(d),
    onTyping: (d) => live.onTyping?.(d),
    onOfflineMessages: (m) => live.onOfflineMessages?.(m),
    onNewNotification: (d) => live.onNewNotification?.(d),
    onNewFriendRequest: (d) => live.onNewFriendRequest?.(d),
    onNewJoinRequest: (d) => live.onNewJoinRequest?.(d),
    onJoinRequestHandled: (d) => live.onJoinRequestHandled?.(d),
  }

  subscriberMap.set(key, proxy)
  subscriberCount++
  if (closed) closed = false
  void connect()

  onUnmounted(() => {
    subscriberMap.delete(key)
    subscriberCount--
    if (subscriberCount === 0) {
      disconnect()
    }
  })

  return {
    connectionState: readonly(connectionState),
    connect,
    sendTyping,
    markConversationRead,
  }
}
