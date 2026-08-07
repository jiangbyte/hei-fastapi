<!-- Author: Charlie -->

<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { messageApi } from '@/api'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const props = defineProps<{ keyword: string }>()
const data = inject(MESSAGE_DATA_KEY)!
const themeVars = useThemeVars()
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const searchResultUsers = ref<any[]>([])
const searchLoading = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const filteredConversations = computed(() => {
  const k = props.keyword.toLowerCase()
  if (!k) return []
  return data.conversations.filter((c) => (c.title ?? '').toLowerCase().includes(k))
})

const filteredGroups = computed(() => {
  const k = props.keyword.toLowerCase()
  if (!k) return []
  return data.groups.filter(
    (g) => g.name.toLowerCase().includes(k) || (g.description ?? '').toLowerCase().includes(k),
  )
})

// 切换到用户标签页时触发 API 搜索
function doSearchUsers() {
  const k = props.keyword
  if (!k) return
  if (searchTimer) clearTimeout(searchTimer)
  searchLoading.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await messageApi.searchUsers(k)
      searchResultUsers.value = res?.data ?? []
    } catch {
      searchResultUsers.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <NTabs
      v-model:value="ui.searchScope.value"
      type="segment"
      size="small"
      class="px-4 pt-3"
      @update:value="doSearchUsers"
    >
      <NTabPane name="conversations" tab="对话">
        <NScrollbar class="h-full">
          <NList v-if="filteredConversations.length" hoverable clickable>
            <NListItem
              v-for="conv in filteredConversations"
              :key="conv.id"
              class="message-list-item cursor-pointer"
              @click="actions.openConversation(conv.id)"
            >
              <div class="message-list-row flex items-start gap-3 px-4 py-3">
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
                <div class="message-list-body">
                  <div class="message-list-main-line flex items-center justify-between gap-3">
                    <span class="message-ellipsis flex-1 text-sm font-600">{{
                      conv.title || '会话'
                    }}</span>
                    <span class="shrink-0 text-xs" :style="{ color: themeVars.textColor3 }">{{
                      formatDateTime(conv.last_message_at ?? conv.created_at)
                    }}</span>
                  </div>
                </div>
              </div>
            </NListItem>
          </NList>
          <NEmpty v-else class="py-12" description="暂无对话结果" />
        </NScrollbar>
      </NTabPane>
      <NTabPane name="users" tab="用户">
        <NScrollbar class="h-full">
          <NList v-if="searchResultUsers.length" hoverable clickable>
            <NListItem
              v-for="user in searchResultUsers"
              :key="`${user.account_type}-${user.account_id}`"
              class="message-list-item"
            >
              <div class="message-list-row flex items-start gap-3 px-4 py-3">
                <NAvatar
                  v-if="user.avatar"
                  round
                  :size="40"
                  class="shrink-0"
                  :src="resolveFileUrl(user.avatar)"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="40" class="shrink-0">
                  {{ (user.name || user.nickname || '?').charAt(0) }}
                </NAvatar>
                <div class="message-list-body">
                  <div class="message-list-main-line flex items-center justify-between gap-3">
                    <span class="message-ellipsis flex-1 text-sm font-600">{{
                      user.name || user.nickname
                    }}</span>
                  </div>
                  <span
                    class="message-ellipsis mt-1 text-xs"
                    :style="{ color: themeVars.textColor3 }"
                    >{{ user.signature || '-' }}</span
                  >
                </div>
                <NTag v-if="user.is_friend" :bordered="false" size="small" type="success">
                  好友
                </NTag>
              </div>
            </NListItem>
          </NList>
          <div
            v-else-if="searchLoading"
            class="py-8 text-center text-sm"
            :style="{ color: themeVars.textColor3 }"
          >
            搜索中...
          </div>
          <NEmpty v-else class="py-12" description="暂无用户结果" />
        </NScrollbar>
      </NTabPane>
      <NTabPane name="groups" tab="群组">
        <NScrollbar class="h-full">
          <NList v-if="filteredGroups.length" hoverable clickable>
            <NListItem
              v-for="group in filteredGroups"
              :key="group.id"
              class="message-list-item cursor-pointer"
              @click="actions.openGroup(group)"
            >
              <div class="message-list-row flex items-start gap-3 px-4 py-3">
                <NAvatar
                  v-if="group.avatar"
                  round
                  :size="40"
                  class="shrink-0"
                  :src="resolveFileUrl(group.avatar)"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="40" class="shrink-0">
                  {{ (group.name || '?').charAt(0) }}
                </NAvatar>
                <div class="message-list-body">
                  <div class="message-list-main-line flex items-center justify-between gap-3">
                    <span class="message-ellipsis flex-1 text-sm font-600">{{ group.name }}</span>
                  </div>
                  <span
                    class="message-ellipsis mt-1 text-xs"
                    :style="{ color: themeVars.textColor3 }"
                    >{{ group.member_count }} 人 · {{ group.description }}</span
                  >
                </div>
              </div>
            </NListItem>
          </NList>
          <NEmpty v-else class="py-12" description="暂无群组结果" />
        </NScrollbar>
      </NTabPane>
    </NTabs>
  </div>
</template>
