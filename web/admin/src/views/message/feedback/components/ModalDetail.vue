<!--
  Author: Charlie

  反馈详情弹窗。
-->
<script setup lang="ts">
import { msgFeedbackApi } from '@/api'
import { createTagColor, dictTypeColor, dictTypeData, displayValue, formatDateTime } from '@/utils'
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
    const response = await msgFeedbackApi.detail({ id })
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
    title="反馈详情"
    style="width: min(760px, 94vw)"
  >
    <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
      <NSpin :show="state.loading">
        <NDescriptions label-placement="left" bordered :column="1">
          <NDescriptionsItem label="反馈内容">
            <div class="whitespace-pre-wrap">
              {{ state.detail.content }}
            </div>
          </NDescriptionsItem>
          <NDescriptionsItem label="分类">
            <NTag
              :color="createTagColor(dictTypeColor('FEEDBACK_CATEGORY', state.detail.category))"
              :bordered="false"
            >
              {{
                dictTypeData('FEEDBACK_CATEGORY', state.detail.category) ||
                displayValue(state.detail.category)
              }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="联系方式">
            {{ displayValue(state.detail.contact) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="附件">
            <NFlex v-if="state.detail.attach_urls?.length" gap="small" vertical>
              <a
                v-for="(url, idx) in state.detail.attach_urls"
                :key="idx"
                :href="url"
                target="_blank"
                class="text-primary"
                >{{ url }}</a
              >
            </NFlex>
            <span v-else class="text-secondary">无</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="状态">
            <NTag
              :color="createTagColor(dictTypeColor('FEEDBACK_STATUS', state.detail.status))"
              :bordered="false"
            >
              {{
                dictTypeData('FEEDBACK_STATUS', state.detail.status) ||
                displayValue(state.detail.status)
              }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="state.detail.reply" label="管理员回复">
            <div class="whitespace-pre-wrap">
              {{ state.detail.reply }}
            </div>
          </NDescriptionsItem>
          <NDescriptionsItem label="提交时间">
            {{ formatDateTime(state.detail.created_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="账号类型">
            {{
              dictTypeData('ACCOUNT_TYPE', state.detail.submitter_account_type) ||
              displayValue(state.detail.submitter_account_type)
            }}
          </NDescriptionsItem>
          <NDescriptionsItem label="提交账号">
            <NFlex align="center" size="small">
              <NAvatar
                v-if="state.detail.submitter_avatar"
                :src="state.detail.submitter_avatar"
                :size="24"
                round
              />
              <NAvatar v-else :size="24" round :color="'#d9d9d9'">
                {{
                  (state.detail.submitter_nickname ||
                    state.detail.submitter_account_id)?.[0]?.toUpperCase()
                }}
              </NAvatar>
              <span>{{
                state.detail.submitter_nickname || state.detail.submitter_account_id
              }}</span>
            </NFlex>
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
