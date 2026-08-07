<!-- Author: Charlie -->

<script setup lang="ts">
import { messageApi } from '@/api'
import { createTagColor, displayValue, formatDateTime } from '@/utils'
import { dictTypeColor, dictTypeData } from '@/utils/dict'
import { reactive } from 'vue'

const emit = defineEmits<{
  changed: [payload: { type: string; id: string }]
}>()

const state = reactive({
  show: false,
  loading: false,
  actionLoading: false,
  source: {} as any,
  detail: {} as any,
})

async function open(source: any) {
  state.source = source ?? {}
  state.detail = {}
  state.show = true
  state.loading = true
  try {
    const response = await messageApi.notificationMyDetail(state.source.id)
    state.detail = response.data ?? {}
  } finally {
    state.loading = false
  }

  const id = state.detail.id || state.source.id
  if (id && !(state.detail.is_read || state.source.is_read)) {
    await messageApi.readNotification({ ids: [id] })
    state.detail.is_read = true
    state.source.is_read = true
    emit('changed', { type: 'notification', id })
  }
}

async function markNotificationRead() {
  const id = state.detail.id || state.source.id
  if (!id) return
  state.actionLoading = true
  try {
    await messageApi.readNotification({ ids: [id] })
    state.detail.is_read = true
    state.source.is_read = true
    emit('changed', { type: 'notification', id })
  } finally {
    state.actionLoading = false
  }
}

defineExpose({ open })
</script>

<template>
  <NModal
    v-model:show="state.show"
    preset="card"
    draggable
    :mask-closable="false"
    title="通知 详情"
    style="width: 720px"
  >
    <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
      <NSpin :show="state.loading">
        <NDescriptions label-placement="left" bordered :column="1">
          <NDescriptionsItem :label="'标题'">
            {{ displayValue(state.detail.title || state.source.title) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'严重级别'">
            <NTag
              :color="createTagColor(dictTypeColor('NOTIFICATION_SEVERITY', state.detail.severity))"
              :bordered="false"
            >
              {{
                dictTypeData('NOTIFICATION_SEVERITY', state.detail.severity) ||
                displayValue(state.detail.severity)
              }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem :label="'状态'">
            <NTag
              :type="state.detail.is_read || state.source.is_read ? 'success' : 'warning'"
              :bordered="false"
            >
              {{ state.detail.is_read || state.source.is_read ? '已读' : '未读' }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem :label="'发布时间'">
            {{ formatDateTime(state.detail.publish_at || state.source.publish_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'内容'">
            {{ displayValue(state.detail.content || state.source.content) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'创建时间'">
            {{ formatDateTime(state.detail.created_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'更新时间'">
            {{ formatDateTime(state.detail.updated_at) }}
          </NDescriptionsItem>
        </NDescriptions>
        <NSpace class="mt-4" justify="end">
          <NButton
            v-if="!(state.detail.is_read || state.source.is_read)"
            type="primary"
            :loading="state.actionLoading"
            @click="markNotificationRead"
          >
            标记已读
          </NButton>
        </NSpace>
      </NSpin>
    </NScrollbar>
  </NModal>
</template>
