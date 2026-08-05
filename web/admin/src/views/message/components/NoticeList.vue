<script setup lang="ts">
import { inject, computed } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, resolveFileUrl } from '@/utils'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
const data = inject(MESSAGE_DATA_KEY)!
const themeVars = useThemeVars()
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const unreadNoticeCount = computed(() => data.notices.filter((n) => !n.is_read).length)

function isIncomingFriend(r: any) {
  return (
    r.recipient_type === data.profile?.account_type &&
    r.recipient_id === data.profile?.account_id
  )
}

const requestBadgeCount = computed(
  () =>
    data.friendRequests.filter((r: any) => r.status === 'PENDING' && isIncomingFriend(r)).length +
    data.pendingGroupJoinRequests.filter((r: any) => r.status === 'PENDING').length,
)

const combinedFriendItems = computed(() => data.friendRequests)

function friendRequestTitle(req: any) {
  if (isIncomingFriend(req)) return req.applicant_name || '好友申请'
  return req.recipient_name || '好友申请'
}

function friendRequestHint(req: any) {
  if (req.status !== 'PENDING') return req.message || '-'
  if (isIncomingFriend(req)) return req.message || '请求添加你为好友'
  return '等待对方处理'
}

const combinedGroupItems = computed(() => {
  const map = new Map<string, any>()
  for (const r of [...data.groupJoinRequests, ...data.pendingGroupJoinRequests]) {
    map.set(r.id, r)
  }
  return [...map.values()].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )
})

function noticeSeverityColor(severity: string) {
  const s = String(severity || '').toLowerCase()
  if (s === 'error') return 'var(--error-color)'
  if (s === 'warning') return 'var(--warning-color)'
  return 'var(--info-color)'
}

function isNoticeSelected(id: string) {
  return ui.selectedNoticeId?.value === id
}

function isPendingSelected(id: string) {
  return ui.selectedPendingRequestId?.value === id
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <NTabs
      v-model:value="ui.noticeTab.value"
      type="segment"
      size="small"
      class="notice-tabs flex min-h-0 flex-1 flex-col px-3 pt-2"
    >
      <NTabPane
        name="notices"
        :tab="unreadNoticeCount ? `通知 (${unreadNoticeCount})` : '通知'"
        class="h-full"
      >
        <NScrollbar class="h-full">
          <div v-if="data.notices.length">
            <div
              v-for="notice in data.notices"
              :key="notice.id"
              class="notice-row flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition-colors"
              :class="{ 'notice-row--active': isNoticeSelected(notice.id) }"
              @click="actions.openNoticeDetail(notice)"
            >
              <NAvatar
                round
                :size="40"
                class="shrink-0"
                :style="{ backgroundColor: noticeSeverityColor(notice.severity) }"
              >
                {{
                  notice.severity === 'error' || notice.severity === 'warning' ? '!' : 'i'
                }}
              </NAvatar>
              <div class="min-w-0 flex-1 overflow-hidden">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
                    <span
                      class="min-w-0 flex-1 truncate text-sm"
                      :class="{ 'font-700': !notice.is_read }"
                      :title="notice.title"
                    >
                      {{ notice.title }}
                    </span>
                    <NTag
                      v-if="!notice.is_read"
                      :bordered="false"
                      size="tiny"
                      type="primary"
                      class="shrink-0"
                    >
                      新
                    </NTag>
                  </div>
                  <span
                    class="shrink-0 whitespace-nowrap text-xs"
                    :style="{ color: themeVars.textColor3 }"
                  >
                    {{ formatDateTime(notice.created_at) }}
                  </span>
                </div>
                <div
                  class="mt-1 truncate text-xs"
                  :style="{ color: themeVars.textColor3 }"
                  :title="notice.content"
                >
                  {{ notice.content }}
                </div>
              </div>
            </div>
          </div>
          <NEmpty v-else class="py-12" description="暂无通知" />
        </NScrollbar>
      </NTabPane>

      <NTabPane
        name="requests"
        :tab="requestBadgeCount ? `申请 (${requestBadgeCount})` : '申请'"
        class="h-full"
      >
        <NScrollbar class="h-full">
          <template v-if="combinedFriendItems.length || combinedGroupItems.length">
            <div
              v-for="req in combinedFriendItems"
              :key="'f-' + req.id"
              class="notice-row relative flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition-colors select-none"
              :class="{ 'notice-row--active': isPendingSelected(req.id) }"
              @click="actions.openPendingDetail(req)"
            >
              <div
                v-if="req.status !== 'PENDING'"
                class="pointer-events-none absolute bottom-2 right-2 z-10 select-none rounded border-2 bg-white px-2 text-[11px] font-700 opacity-70"
                :style="{
                  transform: 'rotate(-15deg)',
                  color: req.status === 'ACCEPTED' ? '#18a058' : '#d03050',
                  borderColor: req.status === 'ACCEPTED' ? '#18a058' : '#d03050',
                }"
              >
                {{ req.status === 'ACCEPTED' ? '已通过' : '已拒绝' }}
              </div>
              <NAvatar
                v-if="isIncomingFriend(req) ? req.applicant_avatar : req.recipient_avatar"
                round
                :size="40"
                class="shrink-0"
                :src="
                  resolveFileUrl(
                    isIncomingFriend(req) ? req.applicant_avatar : req.recipient_avatar,
                  )
                "
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="40" class="shrink-0">
                {{ friendRequestTitle(req)?.charAt(0) || '?' }}
              </NAvatar>
              <div class="min-w-0 flex-1 overflow-hidden">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
                    <span
                      class="min-w-0 flex-1 truncate text-sm font-700"
                      :title="friendRequestTitle(req)"
                    >
                      {{ friendRequestTitle(req) }}
                    </span>
                    <NTag
                      v-if="req.status === 'PENDING' && !isIncomingFriend(req)"
                      :bordered="false"
                      size="tiny"
                      class="shrink-0"
                    >
                      已申请
                    </NTag>
                  </div>
                  <span
                    class="shrink-0 whitespace-nowrap text-xs"
                    :style="{ color: themeVars.textColor3 }"
                  >
                    {{ formatDateTime(req.created_at) }}
                  </span>
                </div>
                <div
                  class="mt-1 truncate text-xs"
                  :style="{ color: themeVars.textColor3 }"
                  :title="friendRequestHint(req)"
                >
                  {{ friendRequestHint(req) }}
                </div>
              </div>
            </div>

            <div
              v-for="req in combinedGroupItems"
              :key="'g-' + req.id"
              class="notice-row relative flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition-colors select-none"
              :class="{ 'notice-row--active': isPendingSelected(req.id) }"
              @click="actions.openPendingDetail(req)"
            >
              <div
                v-if="req.status !== 'PENDING'"
                class="pointer-events-none absolute bottom-2 right-2 z-10 select-none rounded border-2 bg-white px-2 text-[11px] font-700 opacity-70"
                :style="{
                  transform: 'rotate(-15deg)',
                  color: req.status === 'ACCEPTED' ? '#18a058' : '#d03050',
                  borderColor: req.status === 'ACCEPTED' ? '#18a058' : '#d03050',
                }"
              >
                {{ req.status === 'ACCEPTED' ? '已通过' : '已拒绝' }}
              </div>
              <NAvatar
                v-if="req.applicant_avatar"
                round
                :size="40"
                class="shrink-0"
                :src="resolveFileUrl(req.applicant_avatar)"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="40" class="shrink-0">
                {{ req.applicant_name?.charAt(0) || '?' }}
              </NAvatar>
              <div class="min-w-0 flex-1 overflow-hidden">
                <div class="flex items-start justify-between gap-3">
                  <span
                    class="min-w-0 flex-1 truncate text-sm font-700"
                    :title="req.group_name || req.applicant_name || '入群申请'"
                  >
                    {{ req.group_name || req.applicant_name || '入群申请' }}
                  </span>
                  <span
                    class="shrink-0 whitespace-nowrap text-xs"
                    :style="{ color: themeVars.textColor3 }"
                  >
                    {{ formatDateTime(req.created_at) }}
                  </span>
                </div>
                <div
                  class="mt-1 truncate text-xs"
                  :style="{ color: themeVars.textColor3 }"
                  :title="req.message || req.group_name || '-'"
                >
                  {{ req.message || req.group_name || '-' }}
                </div>
              </div>
            </div>
          </template>
          <NEmpty v-else class="py-12" description="暂无待处理申请" />
        </NScrollbar>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.notice-tabs :deep(.n-tabs-pane-wrapper),
.notice-tabs :deep(.n-tab-pane) {
  height: 100%;
  min-height: 0;
}
.notice-tabs :deep(.n-tabs-content) {
  flex: 1 1 0;
  min-height: 0;
}
.notice-row:hover {
  background-color: var(--n-color-hover, rgba(0, 0, 0, 0.04));
}
.notice-row--active {
  background-color: var(--n-color-pressed, rgba(0, 0, 0, 0.06));
}
</style>
