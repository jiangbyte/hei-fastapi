<script setup lang="ts">
import { resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { inject } from 'vue'
import { useThemeVars } from 'naive-ui'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const data = inject(MESSAGE_DATA_KEY)!
const themeVars = useThemeVars()
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <NTabs v-model:value="ui.contactTab.value" type="segment" size="small" class="px-4 pt-3">
      <NTabPane name="friends" tab="好友">
        <NScrollbar class="h-full">
          <NList v-if="data.friends.length" hoverable clickable>
            <NListItem
              v-for="friend in data.friends"
              :key="friend.friendship_id"
              class="message-list-item cursor-pointer"
              @click="actions.openFriend(friend)"
            >
              <div class="message-list-row flex items-start gap-3 px-4 py-3">
                <NAvatar
                  v-if="friend.avatar"
                  round
                  :size="40"
                  class="shrink-0"
                  :src="resolveFileUrl(friend.avatar)"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="40" class="shrink-0">
                  {{ (friend.name || friend.nickname || '?').charAt(0) }}
                </NAvatar>
                <div class="message-list-body">
                  <div class="message-list-main-line flex items-center justify-between gap-3">
                    <span class="message-ellipsis flex-1 text-sm font-600">{{
                      friend.name || friend.nickname || '未知'
                    }}</span>
                    <NTag size="tiny" :bordered="false">
                      {{ friend.friend_account_type === 'PORTAL' ? '学生' : '管理员' }}
                    </NTag>
                  </div>
                  <span
                    class="message-ellipsis mt-1 text-xs"
                    :style="{ color: themeVars.textColor3 }"
                    >{{ friend.signature || '-' }}</span
                  >
                </div>
              </div>
            </NListItem>
          </NList>
          <NEmpty v-else class="py-12" description="暂无好友" />
        </NScrollbar>
      </NTabPane>
      <NTabPane name="groups" tab="群组">
        <NScrollbar class="h-full">
          <NList v-if="data.groups.length" hoverable clickable>
            <NListItem
              v-for="group in data.groups"
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
                    >{{ group.member_count }} 人 · {{ group.description || '-' }}</span
                  >
                </div>
              </div>
            </NListItem>
          </NList>
          <NEmpty v-else class="py-12" description="暂无群组" />
        </NScrollbar>
      </NTabPane>
    </NTabs>
  </div>
</template>
