<script setup lang="ts">
import { computed, inject } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, resolveFileUrl } from '@/utils'
import type { FriendRequest, GroupJoinRequest, Notification } from '../types'
import { MESSAGE_UI_STATE_KEY } from '../provide-keys'

const props = defineProps<{
  request: FriendRequest | GroupJoinRequest | null
  notice: Notification | null
  canHandle: boolean
}>()

const emit = defineEmits<{
  acceptRequest: []
  rejectRequest: []
  close: []
}>()

const themeVars = useThemeVars()
const ui = inject(MESSAGE_UI_STATE_KEY)!
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
const avatarUrl = computed(() => resolveFileUrl(props.request?.applicant_avatar) || undefined)
</script>

<template>
  <NCard
    :bordered="false"
    class="h-full min-h-0 overflow-hidden shadow-sm"
    :content-style="{ height: '100%', padding: '0' }"
  >
    <!-- 申请详情 -->
    <template v-if="request">
      <div class="flex h-full min-h-0 flex-col">
        <NScrollbar class="h-full">
          <div class="mx-auto flex w-full max-w-[460px] flex-col gap-4 px-4 py-6">
            <div v-if="ui.isMobile.value" class="flex justify-start">
              <NButton text size="small" @click="emit('close')">
                <template #icon>
                  <NovaIcon icon="icon-park-outline:arrow-left" :size="18" />
                </template>
              </NButton>
            </div>
            <div class="flex items-center gap-3" style="position: relative; overflow: visible">
              <NAvatar
                v-if="avatarUrl"
                round
                :size="64"
                class="shrink-0"
                :src="avatarUrl"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="64" class="shrink-0">
                {{ (props.request?.applicant_name || '?').charAt(0) }}
              </NAvatar>
              <div
                v-if="request && request.status !== 'PENDING'"
                class="absolute z-10 pointer-events-none select-none"
                style="
                  right: 6px;
                  bottom: 6px;
                  padding: 1px 8px;
                  border-width: 2px;
                  border-style: solid;
                  border-radius: 3px;
                  transform: rotate(-15deg);
                  opacity: 0.7;
                  font-size: 11px;
                  font-weight: 700;
                  line-height: 1.5;
                  background: white;
                "
                :style="
                  request.status === 'ACCEPTED'
                    ? 'color:#18a058;border-color:#18a058;'
                    : 'color:#d03050;border-color:#d03050;'
                "
              >
                {{ request.status === 'ACCEPTED' ? '已通过' : '已拒绝' }}
              </div>
              <div class="min-w-0 text-left">
                <div class="truncate text-lg font-600">
                  {{ 'applicant_name' in request ? request.applicant_name : '申请' }}
                </div>
                <div class="truncate text-xs" :style="{ color: themeVars.textColor3 }">
                  {{ 'group_name' in request ? request.group_name : '好友申请' }}
                </div>
              </div>
            </div>
            <NDescriptions :column="1" label-placement="left" size="small">
              <NDescriptionsItem label="类型">
                {{ 'group_name' in request ? '入群申请' : '好友申请' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="说明">
                {{ 'message' in request ? request.message : '' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="时间">
                {{ formatDateTime(request.created_at) }}
              </NDescriptionsItem>
            </NDescriptions>
            <NFlex justify="center" :wrap="true" :size="12">
              <template v-if="canHandle">
                <NButton type="primary" @click="emit('acceptRequest')"> 通过 </NButton>
                <NButton tertiary type="error" @click="emit('rejectRequest')"> 拒绝 </NButton>
              </template>
              <NTag v-else :bordered="false" size="small">
                {{
                  request?.status === 'ACCEPTED'
                    ? '已通过'
                    : request?.status === 'REJECTED'
                      ? '已拒绝'
                      : '等待对方处理'
                }}
              </NTag>
            </NFlex>
          </div>
        </NScrollbar>
      </div>
    </template>
    <!-- 通知详情 -->
    <template v-else-if="notice">
      <div class="flex h-full min-h-0 flex-col">
        <NScrollbar class="h-full">
          <div class="mx-auto flex w-full max-w-[460px] flex-col gap-4 px-4 py-6">
            <div v-if="ui.isMobile.value" class="flex justify-start">
              <NButton text size="small" @click="emit('close')">
                <template #icon>
                  <NovaIcon icon="icon-park-outline:arrow-left" :size="18" />
                </template>
              </NButton>
            </div>
            <div class="flex items-center gap-3">
              <NAvatar
                round
                :size="64"
                class="shrink-0"
                :style="{
                  backgroundColor:
                    notice.severity === 'error'
                      ? 'var(--error-color)'
                      : notice.severity === 'warning'
                        ? 'var(--warning-color)'
                        : 'var(--primary-color)',
                }"
              >
                {{ notice.severity === 'error' ? '!' : notice.severity === 'warning' ? '!' : 'i' }}
              </NAvatar>
              <div class="min-w-0 text-left">
                <div class="truncate text-lg font-600">
                  {{ notice.title }}
                </div>
                <div class="truncate text-xs" :style="{ color: themeVars.textColor3 }">
                  {{ formatDateTime(notice.created_at) }}
                </div>
              </div>
            </div>
            <NAlert v-if="notice.severity === 'error'" type="error" :bordered="false">
              严重通知
            </NAlert>
            <NAlert v-else-if="notice.severity === 'warning'" type="warning" :bordered="false">
              重要通知
            </NAlert>
            <div
              class="rounded-1 border px-4 py-4 text-sm leading-7 whitespace-pre-wrap"
              :style="{ borderColor: themeVars.borderColor, backgroundColor: themeVars.cardColor }"
            >
              {{ notice.content }}
            </div>
            <NFlex justify="center" :wrap="true" :size="12">
              <NButton @click="emit('close')"> 关闭 </NButton>
            </NFlex>
          </div>
        </NScrollbar>
      </div>
    </template>
    <NEmpty v-else class="grid h-full place-items-center" description="请选择通知项查看" />
  </NCard>
</template>
