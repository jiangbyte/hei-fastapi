<!-- Author: Charlie -->

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { messageApi } from '@/api'
import MessageDetailModal from '@/components/message/MessageDetailModal.vue'
import { formatDateTime } from '@/utils'
import NoticeList, { type BannerItem } from '../common/NoticeList.vue'
import { readPageMeta } from '@/utils/wire'

const pageSize = 8

type LoadMode = 'replace' | 'merge' | 'append'

interface NoticeSource {
  id: string
  title: string
  icon: string
  tagTitle?: string
  tagType?: BannerItem['tagType']
  description?: string
  date: string
  sourceType: string
  sourceId: string
  isRead: boolean
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

const state = reactive(createTabState())
const unreadCount = ref(0)
const detailModalRef = ref<InstanceType<typeof MessageDetailModal> | null>(null)

const list = computed(() => state.records.map(toNoticeItem))
const hasMore = computed(() => state.records.length < state.total)

onMounted(() => {
  void refresh()
})

async function refresh() {
  await Promise.all([refreshUnreadCount(), loadTab(1, state.loaded ? 'merge' : 'replace')])
}

async function refreshUnreadCount() {
  try {
    const nRes = await messageApi.notificationUnreadCount()
    unreadCount.value = nRes.data ?? 0
  } catch {
    /* 忽略 */
  }
}

async function loadMore() {
  if (state.loading || state.records.length >= state.total) return
  await loadTab(state.current + 1, 'append')
}

async function loadTab(page = 1, mode: LoadMode = 'replace') {
  if (state.loading) return
  state.loading = true
  try {
    const response = await messageApi.notificationMyPage({ current: page, size: state.size })
    const data = response.data ?? {}
    const incoming = (data.records ?? []).map((item: any) => mapHistoryItem(item))
    state.records = mergeNoticeRecords(state.records, incoming, mode)
    const pageMeta = readPageMeta(data, { current: page, size: state.size })
    state.total = pageMeta.total || state.records.length
    state.current = pageMeta.current
    state.size = pageMeta.size
    state.loaded = true
  } finally {
    state.loading = false
  }
}

async function handleOpen(id: string) {
  const item = state.records.find((notice) => notice.id === id)
  if (!item) return
  await detailModalRef.value?.open({ ...item, id: item.sourceId, is_read: item.isRead })
}

async function handleDetailChanged(payload: { type: string; id: string }) {
  const item = state.records.find((notice) => notice.id === `${payload.type}:${payload.id}`)
  if (item && !item.isRead) {
    item.isRead = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
  await refreshUnreadCount()
}

async function markAllRead() {
  try {
    await messageApi.readAllNotification()
    state.records.forEach((item) => {
      item.isRead = true
    })
    unreadCount.value = 0
  } catch {
    /* 忽略 */
  }
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

function mapHistoryItem(item: any): NoticeSource {
  return {
    id: `notification:${item.id}`,
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

function toNoticeItem(item: NoticeSource): BannerItem {
  return { ...item, isRead: item.isRead }
}
</script>

<template>
  <n-popover placement="bottom" trigger="click" arrow-point-to-center class="!p-0">
    <template #trigger>
      <n-tooltip placement="bottom" trigger="hover">
        <template #trigger>
          <CommonWrapper>
            <n-badge :value="unreadCount" :max="99" style="color: unset">
              <NovaIcon icon="icon-park-outline:remind" />
            </n-badge>
          </CommonWrapper>
        </template>
        通知
      </n-tooltip>
    </template>
    <div class="w-390px">
      <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <span class="text-sm font-600">通知</span>
        <n-badge type="info" :value="unreadCount" :max="99" :show-zero="false" />
      </div>
      <NoticeList
        :list="list"
        :loading="state.loading"
        :has-more="hasMore"
        @open="handleOpen"
        @load-more="loadMore"
      />
      <div class="border-t border-gray-100 px-3 py-2">
        <n-button block tertiary size="small" :disabled="unreadCount <= 0" @click="markAllRead">
          全部已读
        </n-button>
      </div>
    </div>
  </n-popover>
  <MessageDetailModal ref="detailModalRef" @changed="handleDetailChanged" />
</template>
