<!-- Author: Charlie -->

<script setup lang="ts">
export interface BannerItem {
  avatar?: string | null
  id: string
  type: number
  title: string
  icon: string
  tagTitle?: string
  tagType?: 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning'
  description?: string
  date: string
  isRead?: boolean
}

import { NAvatar } from 'naive-ui'
import { resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

defineProps<{
  list?: BannerItem[]
  loading?: boolean
  hasMore?: boolean
}>()

const emit = defineEmits<{
  open: [id: string]
  loadMore: []
}>()
</script>

<template>
  <n-scrollbar style="height: 400px">
    <n-empty v-if="!loading && !list?.length" class="h-full py-80px" :description="'暂无数据'" />
    <div v-else-if="loading && !list?.length" class="h-full flex items-center justify-center">
      <n-spin size="small" />
    </div>
    <div v-else class="divide-y divide-gray-100/60">
      <div
        v-for="item in list"
        :key="item.id"
        class="flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-gray-100/50 select-none"
        :class="{ 'opacity-50': item.isRead }"
        @click="emit('open', item.id)"
      >
        <NAvatar
          v-if="item.avatar"
          round
          :size="32"
          class="shrink-0"
          :src="resolveFileUrl(item.avatar)"
          :img-props="avatarImgProps"
        />
        <NovaIcon
          v-else
          :icon="item.icon"
          :size="32"
          class="shrink-0"
          style="color: var(--text-color-2)"
        />
        <div class="min-w-0 flex-1">
          <div class="flex items-start justify-between gap-2">
            <span class="text-sm font-600 truncate">{{ item.title }}</span>
            <span v-if="item.tagTitle" class="shrink-0">
              <n-tag :bordered="false" :type="item.tagType || 'default'" size="tiny">{{
                item.tagTitle
              }}</n-tag>
            </span>
          </div>
          <div
            v-if="item.description"
            class="truncate mt-0.5 text-xs"
            style="color: var(--text-color-3)"
          >
            {{ item.description }}
          </div>
          <div class="mt-0.5 text-xs" style="color: var(--text-color-4)">
            {{ item.date }}
          </div>
        </div>
      </div>
      <div v-if="hasMore" class="py-3 text-center">
        <n-button text size="small" :loading="loading" @click.stop="emit('loadMore')">
          加载更多
        </n-button>
      </div>
    </div>
  </n-scrollbar>
</template>
