/** Author: Charlie */

import { create } from 'zustand'
import { wireInt } from '@/utils/wire'
import { imApi } from '@/api'

type ImUnreadState = {
  messageUnread: number
  friendRequestPending: number
  joinRequestPending: number
  loading: boolean
  refresh: () => Promise<void>
  bumpMessage: (delta?: number) => void
  bumpFriendRequest: (delta?: number) => void
  bumpJoinRequest: (delta?: number) => void
  reset: () => void
}

export const useImUnreadStore = create<ImUnreadState>((set, get) => ({
  messageUnread: 0,
  friendRequestPending: 0,
  joinRequestPending: 0,
  loading: false,

  async refresh() {
    if (get().loading) return
    set({ loading: true })
    try {
      const [convRes, reqRes, joinRes] = await Promise.all([
        imApi.conversationList({ current: 1, size: 100 }),
        imApi.myFriendRequestCount(),
        imApi.pendingJoinRequestCount(),
      ])
      const messageUnread = (convRes.data.records ?? []).reduce(
        (sum: number, c: { unread_count?: string }) =>
          sum + (c.unread_count ? wireInt(c.unread_count) : 0),
        0,
      )
      const raw = reqRes.data as { pending_count?: string } | string | undefined
      const friendRequestPending =
        typeof raw === 'string'
          ? wireInt(raw)
          : raw?.pending_count
            ? wireInt(raw.pending_count)
            : 0
      const joinRequestPending =
        joinRes.data != null && joinRes.data !== '' ? wireInt(String(joinRes.data)) : 0
      set({ messageUnread, friendRequestPending, joinRequestPending })
    } catch {
      // 保留原值
    } finally {
      set({ loading: false })
    }
  },

  bumpMessage(delta = 1) {
    set((s) => ({ messageUnread: Math.max(0, s.messageUnread + delta) }))
  },

  bumpFriendRequest(delta = 1) {
    set((s) => ({
      friendRequestPending: Math.max(0, s.friendRequestPending + delta),
    }))
  },

  bumpJoinRequest(delta = 1) {
    set((s) => ({
      joinRequestPending: Math.max(0, s.joinRequestPending + delta),
    }))
  },

  reset() {
    set({
      messageUnread: 0,
      friendRequestPending: 0,
      joinRequestPending: 0,
      loading: false,
    })
  },
}))
