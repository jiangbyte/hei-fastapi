<!--
  Author: Charlie

  通知详情弹窗。
-->
<script setup lang="ts">
import { msgNotificationApi } from '@/api'
import { createTagColor, dictTypeColor, dictTypeData, displayValue, formatDateTime } from '@/utils'
import { MdPreview, RichTextPreview } from '@/components/editor'
import { reactive } from 'vue'

const state = reactive({
  showModal: false,
  loading: false,
  detail: {} as any,
})

async function openModal(id: string) {
  state.detail = {}
  state.showModal = true
  await fetchDetail(id)
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const response = await msgNotificationApi.detail({ id })
    state.detail = response.data ?? {}
  } finally {
    state.loading = false
  }
}

defineExpose({
  openModal,
})
</script>

<template>
  <NModal
    v-model:show="state.showModal"
    preset="card"
    draggable
    :mask-closable="false"
    title="通知详情"
    style="width: min(760px, 94vw)"
  >
    <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
      <NSpin :show="state.loading">
        <NDescriptions label-placement="left" bordered :column="1">
          <NDescriptionsItem label="标题">
            {{ displayValue(state.detail.title) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="内容">
            <div v-if="state.detail.content_type === 'text'" class="whitespace-pre-wrap">
              {{ state.detail.content }}
            </div>
            <MdPreview
              v-else-if="state.detail.content_type === 'markdown'"
              :value="state.detail.content"
              :preview="true"
            />
            <RichTextPreview v-else :value="state.detail.content" />
          </NDescriptionsItem>
          <NDescriptionsItem label="分类">
            {{
              dictTypeData('SYS_BIZ_CATEGORY', state.detail.category) ||
              displayValue(state.detail.category)
            }}
          </NDescriptionsItem>
          <NDescriptionsItem label="等级">
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
          <NDescriptionsItem label="内容格式">
            <NTag bordered="false">
              {{
                dictTypeData('CONTENT_TYPE', state.detail.content_type) ||
                displayValue(state.detail.content_type)
              }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="目标范围">
            {{
              dictTypeData('TARGET_SCOPE', state.detail.target_scope) ||
              displayValue(state.detail.target_scope)
            }}
          </NDescriptionsItem>
          <NDescriptionsItem label="状态">
            <NTag
              :color="createTagColor(dictTypeColor('PUBLISH_STATUS', state.detail.status))"
              :bordered="false"
            >
              {{
                dictTypeData('PUBLISH_STATUS', state.detail.status) ||
                displayValue(state.detail.status)
              }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="发布时间">
            {{ formatDateTime(state.detail.publish_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="创建时间">
            {{ formatDateTime(state.detail.created_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="创建人">
            {{ state.detail.created_name || displayValue(state.detail.created_by) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="更新时间">
            {{ formatDateTime(state.detail.updated_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="更新人">
            {{ state.detail.updated_name || displayValue(state.detail.updated_by) }}
          </NDescriptionsItem>
        </NDescriptions>
      </NSpin>
    </NScrollbar>
  </NModal>
</template>

<style scoped>
.whitespace-pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
