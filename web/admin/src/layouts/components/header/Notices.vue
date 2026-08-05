<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { messageApi } from '@/api'
import MessageDetailModal from '@/components/message/MessageDetailModal.vue'
import { formatDateTime, resolveFileUrl } from '@/utils'
import { NAvatar } from 'naive-ui'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import NoticeList, { type NoticeItem } from '../common/NoticeList.vue'
import { useWebSocket } from '../../../views/message/use-websocket'
import { useImCenterStore } from '@/stores'

const pageSize = 8

type NoticeTab = 0 | 1
type LoadMode = 'replace' | 'merge' | 'append'

interface NoticeSource {
  id: string
  type: NoticeTab
  title: string
  icon: string
  avatar?: string
  unreadCount?: number
  tagTitle?: string
  tagType?: NoticeItem['tagType']
  description?: string
  date: string
  sourceType: string
  sourceId: string
  isRead: boolean
  conversationType?: string
}

interface NoticeTabState {
  records: NoticeSource[]
  current: number
  size: number
  total: number
  loading: boolean
  loaded: boolean
}

function createTabState(): NoticeTabState {
  return { records: [], current: 0, size: pageSize, total: 0, loading: false, loaded: false }
}

const tabStates = reactive<Record<NoticeTab, NoticeTabState>>({
  0: createTabState(),
  1: createTabState(),
})
const unreadCounts = reactive({
  notification: 0,
  message: 0,
  friendRequest: 0,
  joinRequest: 0,
})
const currentTab = ref<NoticeTab>(0)
const detailModalRef = ref<InstanceType<typeof MessageDetailModal> | null>(null)
const imCenterStore = useImCenterStore()

const groups = computed(() => ({
  0: tabStates[0].records.map(toNoticeItem),
  1: tabStates[1].records.map(toNoticeItem),
}))

const hasMore = computed(() => ({
  0: tabStates[0].records.length < tabStates[0].total,
  1: tabStates[1].records.length < tabStates[1].total,
}))

const unreadTotal = computed(
  () =>
    unreadCounts.notification +
    unreadCounts.message +
    unreadCounts.friendRequest +
    unreadCounts.joinRequest,
)

onMounted(() => {
  refresh()
  ws.connect()
})

/* ---- WebSocket 实时更新 ---- */

let wsRefreshTimer: ReturnType<typeof setTimeout> | null = null
function scheduleWsRefresh(delay = 400) {
  if (wsRefreshTimer) clearTimeout(wsRefreshTimer)
  wsRefreshTimer = setTimeout(() => {
    wsRefreshTimer = null
    refresh()
  }, delay)
}

const ws = useWebSocket({
  onNewMessage() {
    unreadCounts.message += 1
    scheduleWsRefresh()
  },
  onNewNotification() {
    unreadCounts.notification += 1
    scheduleWsRefresh()
  },
  onNewFriendRequest() {
    unreadCounts.friendRequest += 1
    scheduleWsRefresh(200)
  },
  onNewJoinRequest() {
    unreadCounts.joinRequest += 1
    scheduleWsRefresh(200)
  },
})

watch(currentTab, (type) => {
  if (!tabStates[type].loaded) loadTab(type)
})

async function refresh() {
  await Promise.all([refreshUnreadCounts(), loadInitialHistories()])
}

async function refreshUnreadCounts() {
  try {
    const nRes = await messageApi.notificationUnreadCount()
    unreadCounts.notification = nRes.data ?? 0
  } catch {
    /* ignore */
  }
  try {
    const convList = await messageApi.conversationList()
    unreadCounts.message = (convList.data?.records ?? []).reduce(
      (s: number, c: any) => s + (c.unread_count ?? 0),
      0,
    )
  } catch {
    /* ignore */
  }
  try {
    const fRes = await messageApi.myFriendRequestCount()
    const raw = fRes.data
    unreadCounts.friendRequest =
      typeof raw === 'number' ? raw : Number(raw?.pending_count ?? 0)
  } catch {
    /* ignore */
  }
  try {
    const jRes = await messageApi.pendingJoinRequestCount()
    unreadCounts.joinRequest = Number(jRes.data ?? 0)
  } catch {
    /* ignore */
  }
}

async function loadInitialHistories() {
  await Promise.all(
    ([0, 1] as NoticeTab[]).map((type) =>
      loadTab(type, 1, tabStates[type].loaded ? 'merge' : 'replace'),
    ),
  )
}

async function loadMore(type: NoticeTab) {
  const state = tabStates[type]
  if (state.loading || state.records.length >= state.total) return
  await loadTab(type, state.current + 1, 'append')
}

async function loadTab(type: NoticeTab, page = 1, mode: LoadMode = 'replace') {
  const state = tabStates[type]
  if (state.loading) return
  state.loading = true
  try {
    const response = await fetchHistoryPage(type, page, state.size)
    const data = response.data ?? {}
    const incoming = (data.records ?? []).map((item: any) => mapHistoryItem(type, item))
    state.records = mergeNoticeRecords(state.records, incoming, mode)
    state.total = data.total ?? state.records.length
    state.current = data.current ?? page
    state.size = data.size ?? state.size
    state.loaded = true
  } finally {
    state.loading = false
  }
}

function fetchHistoryPage(type: NoticeTab, current: number, size: number) {
  if (type === 0) return messageApi.notificationMyPage({ current, size })
  return messageApi.conversationList({ current, size })
}

async function handleOpen(id: string) {
  const item = findNotice(id)
  if (!item) return
  if (item.sourceType === 'message') {
    imCenterStore.open({ conversationId: item.sourceId, section: 'chat' })
    return
  }
  await detailModalRef.value?.open({ ...item, id: item.sourceId, is_read: item.isRead })
}

function openMessageCenter() {
  imCenterStore.open({ section: currentTab.value === 1 ? 'chat' : 'notice' })
}

function findNotice(id: string) {
  for (const type of [0, 1] as NoticeTab[]) {
    const item = tabStates[type].records.find((notice) => notice.id === id)
    if (item) return item
  }
  return null
}

async function handleDetailChanged(payload: { type: string; id: string }) {
  const item = findNotice(`${payload.type}:${payload.id}`)
  if (item && !item.isRead) {
    item.isRead = true
    item.unreadCount = 0
    if (payload.type === 'notification')
      unreadCounts.notification = Math.max(0, unreadCounts.notification - 1)
    else unreadCounts.message = Math.max(0, unreadCounts.message - 1)
  }
  await refreshUnreadCounts()
}

function mergeNoticeRecords(
  current: NoticeSource[],
  incoming: NoticeSource[],
  mode: LoadMode,
): NoticeSource[] {
  if (mode === 'replace') return incoming
  const currentMap = new Map(current.map((item) => [item.id, item]))
  const result = current.map((item) => ({
    ...item,
    ...(incoming.find((i) => i.id === item.id) ?? {}),
  }))
  incoming.forEach((item) => {
    if (!currentMap.has(item.id)) result.push(item)
  })
  return result
}

function mapHistoryItem(type: NoticeTab, item: any): NoticeSource {
  if (type === 0) {
    return {
      id: `notification:${item.id}`,
      type,
      title: item.title,
      icon: 'icon-park-outline:tips-one',
      tagTitle: item.severity,
      tagType: (['success', 'warning', 'error'] as any[]).includes(
        (item.severity || '').toLowerCase(),
      )
        ? ((item.severity || '').toLowerCase() as any)
        : 'info',
      description: item.content,
      date: formatDateTime(item.publish_at || item.created_at),
      sourceType: 'notification',
      sourceId: item.id,
      isRead: Boolean(item.is_read),
    }
  }
  return {
    id: `message:${item.id}`,
    type,
    title: item.title || '会话',
    avatar: item.avatar,
    conversationType: item.conversation_type,
    description: item.last_message || '',
    date: formatDateTime(item.last_message_at || item.created_at),
    sourceType: 'message',
    sourceId: item.id,
    unreadCount: item.unread_count ?? 0,
    isRead: (item.unread_count ?? 0) <= 0,
  }
}

function toNoticeItem(item: NoticeSource): NoticeItem {
  return { ...item, isRead: item.isRead }
}
</script>

<template>
  <n-popover placement="bottom" trigger="click" arrow-point-to-center class="!p-0">
    <template #trigger>
      <n-tooltip placement="bottom" trigger="hover">
        <template #trigger>
          <CommonWrapper>
            <n-badge :value="unreadTotal" :max="99" style="color: unset">
              <NovaIcon icon="icon-park-outline:remind" />
            </n-badge>
          </CommonWrapper>
        </template>
        通知
      </n-tooltip>
    </template>
    <n-tabs
      v-model:value="currentTab"
      type="line"
      animated
      justify-content="space-evenly"
      class="w-390px"
    >
      <n-tab-pane :name="0">
        <template #tab>
          <n-space class="w-195px" justify="center">
            通知<n-badge
              type="info"
              :value="unreadCounts.notification"
              :max="99"
              :show-zero="false"
            />
          </n-space>
        </template>
        <NoticeList
          :list="groups[0]"
          :loading="tabStates[0].loading"
          :has-more="hasMore[0]"
          @open="handleOpen"
          @load-more="loadMore(0)"
        />
      </n-tab-pane>
      <n-tab-pane :name="1">
        <template #tab>
          <n-space class="w-195px" justify="center">
            消息<n-badge
              type="warning"
              :value="unreadCounts.message"
              :max="99"
              :show-zero="false"
            />
          </n-space>
        </template>
        <n-scrollbar style="height: 400px">
          <div class="divide-y divide-gray-100/60">
            <div
              v-for="conv in tabStates[1].records"
              :key="conv.id"
              class="flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-gray-50/50 select-none"
              @click="handleOpen(conv.id)"
            >
              <NAvatar
                v-if="conv.avatar"
                round
                :size="40"
                class="shrink-0"
                :src="resolveFileUrl(conv.avatar)"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="40" class="shrink-0">
                {{ conv.title?.charAt(0) || '?' }}
              </NAvatar>
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="message-ellipsis text-sm font-600">{{ conv.title }}</span>
                      <n-badge
                        v-if="conv.unreadCount"
                        type="error"
                        :value="conv.unreadCount"
                        :max="99"
                      />
                    </div>
                  </div>
                  <span class="shrink-0 text-xs" style="color: var(--text-color-3)">{{
                    conv.date
                  }}</span>
                </div>
                <div
                  v-if="conv.description"
                  class="message-ellipsis mt-0.5 text-xs"
                  style="color: var(--text-color-3)"
                >
                  {{ conv.description }}
                </div>
              </div>
            </div>
            <div v-if="hasMore[1]" class="py-3 text-center">
              <n-button text size="small" :loading="tabStates[1].loading" @click.stop="loadMore(1)">
                加载更多
              </n-button>
            </div>
          </div>
        </n-scrollbar>
      </n-tab-pane>
    </n-tabs>
    <div class="border-t border-gray-100 px-3 py-2">
      <n-button block tertiary size="small" @click="openMessageCenter"> 打开消息中心 </n-button>
    </div>
  </n-popover>
  <MessageDetailModal ref="detailModalRef" @changed="handleDetailChanged" />
</template>
