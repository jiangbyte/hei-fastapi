/** Author: Charlie */

import { useEffect, useRef } from 'react'

export type ImWsHandlers = {
  onNewMessage?: (data: any) => void
  onOfflineMessages?: (messages: any[]) => void
  onNewNotification?: (data: any) => void
  onNewFriendRequest?: (data: any) => void
  onNewJoinRequest?: (data: any) => void
  onJoinRequestHandled?: (data: any) => void
  onKick?: () => void
  onOpen?: () => void
  onClose?: () => void
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
  return { cmd, seq, ack, body: new Uint8Array(data, HEADER_SIZE, len) }
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

function wsUrl() {
  const configured = (import.meta.env.VITE_IM_WS_URL as string | undefined)?.trim()
  const tid = encodeURIComponent(terminalId())
  const qs = `terminal_id=${tid}&channel=portal`
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

const subscriberMap = new Map<symbol, ImWsHandlers>()
let subscriberCount = 0
let ws: WebSocket | null = null
let heartbeat: ReturnType<typeof setInterval> | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let disconnectTimer: ReturnType<typeof setTimeout> | null = null
let connectPromise: Promise<void> | null = null
let attempt = 0
let closed = false

function sendFrame(cmd: number, body?: Uint8Array, seq = 0, ack = 0) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(encodeFrame(cmd, body, seq, ack))
  }
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
      default:
        break
    }
  })
}

function handleFrame(cmd: number, seq: number, body: Uint8Array) {
  if (seq > 0) {
    sendFrame(ImCmd.ACK, jsonBody({ seq }), 0, seq)
  }
  if (cmd === ImCmd.PONG || cmd === ImCmd.AUTH_OK) return
  if (cmd === ImCmd.AUTH_FAIL || cmd === ImCmd.KICK) {
    closed = true
    cleanupSocket()
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
    return
  }
  if (cmd === ImCmd.PUSH) {
    const data = parseBody(body)
    dispatchPush(Number(data.event), data.payload)
  }
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
      // 忽略
    }
    ws = null
  }
}

function connect() {
  if (closed) return
  if (connectPromise) return connectPromise
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return

  connectPromise = (async () => {
    let authToken = ''
    try {
      const { imApi } = await import('@/api')
      const res = await imApi.imTicket()
      if (res?.data?.ticket) authToken = res.data.ticket
    } catch {
      connectPromise = null
      return
    }
    if (!authToken) {
      connectPromise = null
      return
    }

    await new Promise<void>((resolve) => {
      cleanupSocket()
      ws = new WebSocket(wsUrl())
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        sendFrame(
          ImCmd.AUTH,
          jsonBody({
            token: authToken,
            terminal_id: terminalId(),
            channel: 'portal',
          }),
        )
        attempt = 0
        connectPromise = null
        subscriberMap.forEach((h) => h.onOpen?.())
        heartbeat = setInterval(() => sendFrame(ImCmd.PING), 25000)
        sendFrame(ImCmd.PULL_OFFLINE)
        resolve()
      }

      ws.onmessage = (event) => {
        if (!(event.data instanceof ArrayBuffer)) return
        try {
          const frame = decodeFrame(event.data)
          handleFrame(frame.cmd, frame.seq, frame.body)
        } catch {
          // 忽略
        }
      }

      ws.onclose = () => {
        connectPromise = null
        cleanupSocket()
        subscriberMap.forEach((h) => h.onClose?.())
        if (!closed) {
          const delay = Math.min(1000 * Math.pow(2, attempt++), 30000)
          reconnectTimer = setTimeout(() => connect(), delay)
        }
      }

      ws.onerror = () => {
        connectPromise = null
        try {
          ws?.close()
        } catch {
          // 忽略
        }
      }
    })
  })()

  return connectPromise
}

function disconnect() {
  closed = true
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  cleanupSocket()
}

export function useImWebSocket(enabled: boolean, handlers: ImWsHandlers) {
  const keyRef = useRef<symbol | null>(null)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  useEffect(() => {
    if (!enabled) {
      if (keyRef.current) {
        subscriberMap.delete(keyRef.current)
        subscriberCount = Math.max(0, subscriberCount - 1)
        keyRef.current = null
        if (subscriberCount === 0) {
          if (disconnectTimer) clearTimeout(disconnectTimer)
          disconnectTimer = setTimeout(() => {
            if (subscriberCount === 0) disconnect()
          }, 500)
        }
      }
      return
    }

    closed = false
    const key = Symbol()
    keyRef.current = key
    subscriberMap.set(key, {
      onNewMessage: (d) => handlersRef.current.onNewMessage?.(d),
      onOfflineMessages: (m) => handlersRef.current.onOfflineMessages?.(m),
      onNewNotification: (d) => handlersRef.current.onNewNotification?.(d),
      onNewFriendRequest: (d) => handlersRef.current.onNewFriendRequest?.(d),
      onNewJoinRequest: (d) => handlersRef.current.onNewJoinRequest?.(d),
      onJoinRequestHandled: (d) => handlersRef.current.onJoinRequestHandled?.(d),
      onKick: () => handlersRef.current.onKick?.(),
      onOpen: () => handlersRef.current.onOpen?.(),
      onClose: () => handlersRef.current.onClose?.(),
    })
    subscriberCount++
    if (disconnectTimer) {
      clearTimeout(disconnectTimer)
      disconnectTimer = null
    }
    void connect()

    return () => {
      subscriberMap.delete(key)
      subscriberCount = Math.max(0, subscriberCount - 1)
      keyRef.current = null
      if (subscriberCount === 0) {
        disconnectTimer = setTimeout(() => {
          if (subscriberCount === 0) disconnect()
        }, 500)
      }
    }
  }, [enabled])
}
