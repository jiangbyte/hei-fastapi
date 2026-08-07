<!-- Author: Charlie -->

<script setup lang="ts">
import { computed, inject } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { MESSAGE_ACTIONS_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const data = inject(MESSAGE_DATA_KEY)!
const themeVars = useThemeVars()
const actions = inject(MESSAGE_ACTIONS_KEY)!

const sortedConversations = computed(() =>
  [...data.conversations].sort((a, b) => {
    const ta = a.last_message_at ?? a.created_at ?? ''
    const tb = b.last_message_at ?? b.created_at ?? ''
    return new Date(tb).getTime() - new Date(ta).getTime()
  }),
)

function getConversationPreview(convId: string, conversation: any): string {
  const msgs = data.messagesByConversation[convId]
  if (msgs?.length) {
    const latest = msgs[msgs.length - 1]
    const prefix =
      latest.sender_nickname || latest.sender_name
        ? `${latest.sender_nickname || latest.sender_name}：`
        : ''
    return `${prefix}${latest.content}`
  }
  return conversation.title ?? ''
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <NScrollbar class="h-full">
      <NList v-if="sortedConversations.length" hoverable clickable>
        <NListItem
          v-for="conv in sortedConversations"
          :key="conv.id"
          class="message-list-item cursor-pointer"
          :style="
            conv.id === (data as any).selectedConversationId
              ? { backgroundColor: themeVars.buttonColor2Hover }
              : {}
          "
          @click="actions.openConversation(conv.id)"
        >
          <div class="message-list-row flex items-start gap-3 px-4 py-3">
            <NBadge class="shrink-0" :value="conv.unread_count" :max="99" :show-zero="false">
              <NAvatar
                v-if="conv.avatar"
                round
                :size="40"
                class="shrink-0"
                :src="resolveFileUrl(conv.avatar)"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="40" class="shrink-0">
                {{ (conv.title || '?').charAt(0) }}
              </NAvatar>
            </NBadge>
            <div class="message-list-body">
              <div class="message-list-main-line flex items-center justify-between gap-3">
                <span class="message-ellipsis flex-1 text-sm font-600">{{
                  conv.title || '会话'
                }}</span>
                <span class="shrink-0 text-xs" :style="{ color: themeVars.textColor3 }">{{
                  formatDateTime(conv.last_message_at ?? conv.created_at)
                }}</span>
              </div>
              <span
                class="message-ellipsis mt-1 text-xs"
                :style="{ color: themeVars.textColor3 }"
                >{{ getConversationPreview(conv.id, conv) }}</span
              >
            </div>
          </div>
        </NListItem>
      </NList>
      <NEmpty v-else class="py-12" description="暂无会话" />
    </NScrollbar>
  </div>
</template>
