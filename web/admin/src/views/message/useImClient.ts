/** Author: Charlie */

import { ref, onUnmounted, readonly, type Ref } from 'vue'

export type ImConnectionState = 'connecting' | 'connected' | 'disconnected'

export interface ImHandlers {
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
  onKick?: () => void
}

const ImCmd = {
  AUTH: 1,
  AUTH_OK: 2,
  AUTH_FAIL: 3,
  PING: 4,
  PONG: 5,
  ACK: 6,
  KICK: 7,
  PUSH: 8,
  PULL_OFFLINE: 9,
  OFFLINE_BATCH: 10,
  READ_CONVERSATION: 11,
  TYPING: 12,
} as const

const PushEvent = {
  MESSAGE: 1,
  NOTIFICATION: 2,
  FRIEND_REQUEST: 3,
  GROUP_JOIN_REQUEST: 4,
  GROUP_JOIN_HANDLED: 5,
  MESSAGE_REVOKED: 6,
} as const

const MAGIC = 0x4849
const HEADER_SIZE = 26

function encodeFrame(cmd: number, body: Uint8Array = new Uint8Array(), seq = 0, ack = 0): ArrayBuffer {
  const buf = new ArrayBuffer(HEADER_SIZE + body.byteLength)
  const view = new DataView(buf)
  view.setUint16(0, MAGIC)
  view.setUint8(2, 1)
  view.setUint16(3, cmd)
  view.setUint8(5, 0)
  view.setBigUint64(6, BigInt(seq))
  view.setBigUint64(14, BigInt(ack))
  view.setUint32(22, body.byteLength)
  new Uint8Array(buf, HEADER_SIZE).set(body)
  return buf
}

function decodeFrame(data: ArrayBuffer): { cmd: number; seq: number; ack: number; body: Uint8Array } {
  const view = new DataView(data)
  if (view.getUint16(0) !== MAGIC) throw new Error('bad magic')
  const cmd = view.getUint16(3)
  const seq = Number(view.getBigUint64(6))
  const ack = Number(view.getBigUint64(14))
  const len = view.getUint32(22)
  const body = new Uint8Array(data, HEADER_SIZE, len)
  return { cmd, seq, ack, body }
}

function jsonBody(obj: unknown): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(obj))
}

function parseBody(body: Uint8Array): any {
  if (!body.byteLength) return {}
  return JSON.parse(new TextDecoder().decode(body))
}

function terminalId(): string {
  const key = 'im_terminal_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = `web-${crypto.randomUUID()}`
    localStorage.setItem(key, id)
  }
  return id
}

function imWsUrl(): string {
  const configured = (import.meta.env.VITE_IM_WS_URL as string | undefined)?.trim()
  const tid = encodeURIComponent(terminalId())
  const qs = `terminal_id=${tid}&channel=admin`
  if (configured) {
    const sep = configured.includes('?') ? '&' : '?'
    return `${configured}${sep}${qs}`
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  if (import.meta.env.PROD) {
    return `${proto}//${window.location.host}/ws?${qs}`
  }
  return `${proto}//${window.location.hostname}:18080/ws?${qs}`
}

const connectionState: Ref<ImConnectionState> = ref('disconnected')
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let reconnectAttempt = 0
let closed = false
let lastServerSeq = 0
const subscriberMap = new Map<symbol, ImHandlers>()
let subscriberCount = 0
let connectPromise: Promise<void> | null = null

function sendFrame(cmd: number, body?: Uint8Array, seq = 0, ack = 0) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(encodeFrame(cmd, body, seq, ack))
  }
}

function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = setInterval(() => {
    sendFrame(ImCmd.PING)
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

function dispatchPush(event: number, payload: any) {
  subscriberMap.forEach((handlers) => {
    switch (event) {
      case PushEvent.MESSAGE:
        handlers.onNewMessage?.(payload)
        break
      case PushEvent.NOTIFICATION:
        handlers.onNewNotification?.(payload)
        break
      case PushEvent.FRIEND_REQUEST:
        handlers.onNewFriendRequest?.(payload)
        break
      case PushEvent.GROUP_JOIN_REQUEST:
        handlers.onNewJoinRequest?.(payload)
        break
      case PushEvent.GROUP_JOIN_HANDLED:
        handlers.onJoinRequestHandled?.(payload)
        break
      case PushEvent.MESSAGE_REVOKED:
        handlers.onNewMessage?.(payload)
        break
      default:
        break
    }
  })
}

function handleFrame(cmd: number, seq: number, body: Uint8Array) {
  if (seq > 0) {
    lastServerSeq = Math.max(lastServerSeq, seq)
    sendFrame(ImCmd.ACK, jsonBody({ seq }), 0, seq)
  }
  if (cmd === ImCmd.PONG || cmd === ImCmd.AUTH_OK) return
  if (cmd === ImCmd.AUTH_FAIL || cmd === ImCmd.KICK) {
    closed = true
    stopHeartbeat()
    try {
      ws?.close()
    } catch {
      /* 忽略 */
    }
    subscriberMap.forEach((h) => h.onKick?.())
    return
  }
  if (cmd === ImCmd.OFFLINE_BATCH) {
    const data = parseBody(body)
    const items = (data.items || []) as Array<{ event?: number; payload?: any }>
    const messages = items
      .filter((i) => i.event === PushEvent.MESSAGE)
      .map((i) => i.payload)
    subscriberMap.forEach((h) => h.onOfflineMessages?.(messages))
    for (const item of items) {
      if (item.event && item.event !== PushEvent.MESSAGE) {
        dispatchPush(item.event, item.payload)
      }
    }
    return
  }
  if (cmd === ImCmd.TYPING) {
    const data = parseBody(body)
    subscriberMap.forEach((h) => h.onTyping?.(data))
    return
  }
  if (cmd === ImCmd.PUSH) {
    const data = parseBody(body)
    dispatchPush(Number(data.event), data.payload)
  }
}

function connect() {
  if (closed && subscriberCount > 0) closed = false
  if (closed) return
  if (connectPromise) return connectPromise
  if (ws?.readyState === WebSocket.OPEN) return
  if (ws?.readyState === WebSocket.CONNECTING) return

  connectionState.value = 'connecting'
  connectPromise = (async () => {
    let authToken = ''
    try {
      const { messageApi } = await import('@/api')
      const res = await messageApi.imTicket()
      if (res?.data?.ticket) authToken = res.data.ticket
    } catch {
      connectionState.value = 'disconnected'
      connectPromise = null
      return
    }
    if (!authToken) {
      connectionState.value = 'disconnected'
      connectPromise = null
      return
    }

    await new Promise<void>((resolve) => {
      ws = new WebSocket(imWsUrl())
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        sendFrame(
          ImCmd.AUTH,
          jsonBody({
            token: authToken,
            terminal_id: terminalId(),
            channel: 'admin',
          }),
        )
        connectionState.value = 'connected'
        reconnectAttempt = 0
        connectPromise = null
        startHeartbeat()
        sendFrame(ImCmd.PULL_OFFLINE)
        resolve()
      }

      ws.onmessage = (event) => {
        if (!(event.data instanceof ArrayBuffer)) return
        try {
          const frame = decodeFrame(event.data)
          handleFrame(frame.cmd, frame.seq, frame.body)
        } catch {
          // 忽略格式错误
        }
      }

      ws.onclose = (event: CloseEvent) => {
        connectPromise = null
        connectionState.value = 'disconnected'
        stopHeartbeat()
        if (event.code === 4001 || event.code === 4002) {
          closed = true
          return
        }
        scheduleReconnect()
      }

      ws.onerror = () => {
        connectPromise = null
        try {
          ws?.close()
        } catch {
          /* 忽略 */
        }
        scheduleReconnect()
      }
    })
  })()

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
  sendFrame(ImCmd.TYPING, jsonBody({ conversation_id: conversationId, is_typing: isTyping }))
}

function markConversationRead(conversationId: string, lastReadMessageId: string) {
  sendFrame(
    ImCmd.READ_CONVERSATION,
    jsonBody({ conversation_id: conversationId, last_read_message_id: lastReadMessageId }),
  )
}

export function useImClient(handlers: ImHandlers) {
  const key = Symbol()
  const live = handlers
  const proxy: ImHandlers = {
    onNewMessage: (d) => live.onNewMessage?.(d),
    onTyping: (d) => live.onTyping?.(d),
    onOfflineMessages: (m) => live.onOfflineMessages?.(m),
    onNewNotification: (d) => live.onNewNotification?.(d),
    onNewFriendRequest: (d) => live.onNewFriendRequest?.(d),
    onNewJoinRequest: (d) => live.onNewJoinRequest?.(d),
    onJoinRequestHandled: (d) => live.onJoinRequestHandled?.(d),
    onKick: () => live.onKick?.(),
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
