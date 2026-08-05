<script setup lang="ts">
import { computed, inject } from 'vue'
import { resolveFileUrl } from '@/utils'
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

const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
const avatarUrl = computed(() => resolveFileUrl(data.profile?.avatar))
</script>

<template>
  <aside
    class="flex h-full min-h-0 flex-col items-center py-3"
    style="background-color: #2b2b2b"
  >
    <NAvatar
      v-if="avatarUrl"
      round
      :size="40"
      :src="avatarUrl"
      :img-props="avatarImgProps"
      class="shrink-0 cursor-pointer"
      @click="actions.openProfileModal()"
    />
    <NAvatar
      v-else
      round
      :size="40"
      class="shrink-0 cursor-pointer"
      @click="actions.openProfileModal()"
    >
      <NovaIcon icon="icon-park-outline:user" :size="20" />
    </NAvatar>

    <div class="mt-6 flex flex-1 flex-col items-center gap-6">
      <NTooltip placement="right">
        <template #trigger>
          <NBadge :value="totalUnreadCount" :max="99" :show-zero="false">
            <NButton
              text
              :class="
                ui.activeSection.value === 'chat' ? 'text-[var(--primary-color)]' : 'text-white'
              "
              aria-label="聊天"
              @click="actions.openChatSection()"
            >
              <template #icon>
                <NovaIcon icon="icon-park-outline:message" :size="22" />
              </template>
            </NButton>
          </NBadge>
        </template>
        聊天
      </NTooltip>

      <NTooltip placement="right">
        <template #trigger>
          <NButton
            text
            :class="
              ui.activeSection.value === 'contacts' ? 'text-[var(--primary-color)]' : 'text-white'
            "
            aria-label="通讯录"
            @click="actions.openContactsSection()"
          >
            <template #icon>
              <NovaIcon icon="icon-park-outline:people" :size="22" />
            </template>
          </NButton>
        </template>
        通讯录
      </NTooltip>

      <NTooltip placement="right">
        <template #trigger>
          <NBadge :value="noticeBadgeTotal" :max="99" :show-zero="false">
            <NButton
              text
              :class="
                ui.activeSection.value === 'notice' ? 'text-[var(--primary-color)]' : 'text-white'
              "
              aria-label="通知"
              @click="actions.openNoticeSection()"
            >
              <template #icon>
                <NovaIcon icon="icon-park-outline:alarm" :size="22" />
              </template>
            </NButton>
          </NBadge>
        </template>
        通知
      </NTooltip>
    </div>

    <div class="mt-auto">
      <NTooltip placement="right">
        <template #trigger>
          <NButton text class="text-white" aria-label="返回工作台" @click="actions.goHome()">
            <template #icon>
              <NovaIcon icon="icon-park-outline:arrow-left" :size="20" />
            </template>
          </NButton>
        </template>
        返回工作台
      </NTooltip>
    </div>
  </aside>
</template>
