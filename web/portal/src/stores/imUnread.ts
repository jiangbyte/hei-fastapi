import { create } from 'zustand'
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
        (sum: any, c: any) => sum + (c.unread_count || 0),
        0,
      )
      const raw = reqRes.data as any
      const friendRequestPending =
        typeof raw === 'number' ? raw : Number(raw?.pending_count ?? 0)
      const joinRequestPending = Number(joinRes.data ?? 0)
      set({ messageUnread, friendRequestPending, joinRequestPending })
    } catch {
      // keep previous
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
