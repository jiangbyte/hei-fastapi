<script setup lang="ts">
import { inject, computed } from 'vue'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const data = inject(MESSAGE_DATA_KEY)!
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const totalUnreadCount = computed(() =>
  data.conversations.reduce((s, c) => s + (c.unread_count || 0), 0),
)
const requestBadgeCount = computed(
  () =>
    data.friendRequests.filter(
      (r: any) =>
        r.status === 'PENDING' &&
        r.recipient_type === data.profile?.account_type &&
        r.recipient_id === data.profile?.account_id,
    ).length +
    data.groupJoinRequests.filter((r: any) => r.status === 'PENDING').length +
    data.pendingGroupJoinRequests.length,
)
const unreadNoticeCount = computed(() => data.notices.filter((n) => !n.is_read).length)
const noticeBadgeTotal = computed(() => requestBadgeCount.value + unreadNoticeCount.value)
</script>

<template>
  <div
    class="border-t md:hidden"
    :style="{ borderColor: 'var(--border-color)', backgroundColor: 'var(--body-color)' }"
  >
    <div class="flex items-center justify-around py-1">
      <NButton
        text
        :class="
          ui.activeSection.value === 'chat'
            ? 'text-[var(--primary-color)]'
            : 'text-[var(--text-color-3)]'
        "
        style="flex-direction: column; height: auto; gap: 2px; padding: 4px 12px"
        @click="actions.openChatSection()"
      >
        <template #icon>
          <NBadge :value="totalUnreadCount" :max="99" :show-zero="false">
            <NovaIcon icon="icon-park-outline:message" :size="20" />
          </NBadge>
        </template>
        <span style="font-size: 10px; line-height: 1">聊天</span>
      </NButton>
      <NButton
        text
        :class="
          ui.activeSection.value === 'contacts'
            ? 'text-[var(--primary-color)]'
            : 'text-[var(--text-color-3)]'
        "
        style="flex-direction: column; height: auto; gap: 2px; padding: 4px 12px"
        @click="actions.openContactsSection()"
      >
        <template #icon>
          <NovaIcon icon="icon-park-outline:people" :size="20" />
        </template>
        <span style="font-size: 10px; line-height: 1">通讯录</span>
      </NButton>
      <NButton
        text
        :class="
          ui.activeSection.value === 'notice'
            ? 'text-[var(--primary-color)]'
            : 'text-[var(--text-color-3)]'
        "
        style="flex-direction: column; height: auto; gap: 2px; padding: 4px 12px"
        @click="actions.openNoticeSection()"
      >
        <template #icon>
          <NBadge :value="noticeBadgeTotal" :max="99" :show-zero="false">
            <NovaIcon icon="icon-park-outline:alarm" :size="20" />
          </NBadge>
        </template>
        <span style="font-size: 10px; line-height: 1">通知</span>
      </NButton>
      <NButton
        text
        :class="
          ui.activeSection.value === 'profile'
            ? 'text-[var(--primary-color)]'
            : 'text-[var(--text-color-3)]'
        "
        style="flex-direction: column; height: auto; gap: 2px; padding: 4px 12px"
        @click="actions.openProfileSection()"
      >
        <template #icon>
          <NovaIcon icon="icon-park-outline:user" :size="20" />
        </template>
        <span style="font-size: 10px; line-height: 1">我的</span>
      </NButton>
    </div>
  </div>
</template>
