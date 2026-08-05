import { useEffect, useRef } from 'react'
import { getToken } from '@/utils/storage'

export type ImWsHandlers = {
  onNewMessage?: (data: any) => void
  onOfflineMessages?: (messages: any[]) => void
  onNewNotification?: (data: any) => void
  onNewFriendRequest?: (data: any) => void
  onNewJoinRequest?: (data: any) => void
  onJoinRequestHandled?: (data: any) => void
  onOpen?: () => void
  onClose?: () => void
}

function wsUrl(token: string) {
  const baseURL = import.meta.env.VITE_API_URL || ''
  if (baseURL.startsWith('http')) {
    return `${baseURL.replace(/^http/, 'ws')}/api/v1/portal/message/ws?token=${encodeURIComponent(token)}`
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/api/v1/portal/message/ws?token=${encodeURIComponent(token)}`
}

/* ---- module-level singleton ---- */

const subscriberMap = new Map<symbol, ImWsHandlers>()
let subscriberCount = 0
let ws: WebSocket | null = null
let heartbeat: ReturnType<typeof setInterval> | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let disconnectTimer: ReturnType<typeof setTimeout> | null = null
let connectPromise: Promise<void> | null = null
let attempt = 0
let closed = false
let activeToken: string | null = null

function dispatch(msg: { type: string; data?: any }) {
  subscriberMap.forEach((handlers) => {
    switch (msg.type) {
      case 'new_message':
        handlers.onNewMessage?.(msg.data)
        break
      case 'offline_messages':
        handlers.onOfflineMessages?.(msg.data?.messages ?? [])
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
      default:
        break
    }
  })
}

function cleanupSocket() {
  if (heartbeat) {
    clearInterval(heartbeat)
    heartbeat = null
  }
  if (ws) {
    ws.onopen = null
    ws.onclose = null
    ws.onmessage = null
    ws.onerror = null
    try {
      ws.close()
    } catch {
      // ignore
    }
    ws = null
  }
}

function connect() {
  if (closed) return
  if (connectPromise) return connectPromise
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return

  const token = activeToken || getToken()
  if (!token) return
  activeToken = token

  connectPromise = new Promise<void>((resolve) => {
    cleanupSocket()
    ws = new WebSocket(wsUrl(token))

    ws.onopen = () => {
      attempt = 0
      connectPromise = null
      subscriberMap.forEach((h) => h.onOpen?.())
      heartbeat = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 25000)
      ws?.send(JSON.stringify({ type: 'pull_offline' }))
      resolve()
    }

    ws.onmessage = (event) => {
      try {
        dispatch(JSON.parse(event.data))
      } catch {
        // ignore
      }
    }

    ws.onclose = () => {
      connectPromise = null
      subscriberMap.forEach((h) => h.onClose?.())
      if (heartbeat) {
        clearInterval(heartbeat)
        heartbeat = null
      }
      if (closed || subscriberCount === 0) return
      const delay = Math.min(1000 * 2 ** attempt, 30000)
      attempt += 1
      reconnectTimer = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      connectPromise = null
      try {
        ws?.close()
      } catch {
        // ignore
      }
    }
  })

  return connectPromise
}

function disconnect() {
  closed = true
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (disconnectTimer) {
    clearTimeout(disconnectTimer)
    disconnectTimer = null
  }
  connectPromise = null
  cleanupSocket()
  activeToken = null
  attempt = 0
}

function scheduleDisconnect() {
  if (disconnectTimer) clearTimeout(disconnectTimer)
  disconnectTimer = setTimeout(() => {
    disconnectTimer = null
    if (subscriberCount === 0) disconnect()
  }, 1500)
}

/** Portal IM WebSocket：单例连接 / 心跳 / 重连，多组件可订阅 */
export function useImWebSocket(enabled: boolean, handlers: ImWsHandlers) {
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers
  const keyRef = useRef<symbol | null>(null)

  useEffect(() => {
    if (!enabled) {
      if (keyRef.current) {
        subscriberMap.delete(keyRef.current)
        subscriberCount = Math.max(0, subscriberCount - 1)
        keyRef.current = null
        if (subscriberCount === 0) scheduleDisconnect()
      }
      return
    }

    if (disconnectTimer) {
      clearTimeout(disconnectTimer)
      disconnectTimer = null
    }
    closed = false
    const key = Symbol()
    keyRef.current = key
    const proxy: ImWsHandlers = {
      onNewMessage: (d) => handlersRef.current.onNewMessage?.(d),
      onOfflineMessages: (m) => handlersRef.current.onOfflineMessages?.(m),
      onNewNotification: (d) => handlersRef.current.onNewNotification?.(d),
      onNewFriendRequest: (d) => handlersRef.current.onNewFriendRequest?.(d),
      onNewJoinRequest: (d) => handlersRef.current.onNewJoinRequest?.(d),
      onJoinRequestHandled: (d) => handlersRef.current.onJoinRequestHandled?.(d),
      onOpen: () => handlersRef.current.onOpen?.(),
      onClose: () => handlersRef.current.onClose?.(),
    }
    subscriberMap.set(key, proxy)
    subscriberCount += 1
    connect()

    return () => {
      subscriberMap.delete(key)
      subscriberCount = Math.max(0, subscriberCount - 1)
      keyRef.current = null
      if (subscriberCount === 0) scheduleDisconnect()
    }
  }, [enabled])
}
