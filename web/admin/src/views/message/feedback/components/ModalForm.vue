<!--
  Author: Charlie

  反馈编辑弹窗 — 仅更新状态与回复。
-->
<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import { msgFeedbackApi } from '@/api'
import { createRequiredRule } from '@/utils'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits<{ saved: [] }>()

const formRef = ref<FormInst | null>(null)
const defaultFormData: Record<string, any> = {
  status: 'PENDING',
  reply: null,
}
const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  dataId: null as string | null,
  formModel: { ...defaultFormData },
})

const modalTitle = computed(() => '处理反馈')
const rules = computed<FormRules>(() => ({
  status: [createRequiredRule('状态', 'change')],
}))

async function openModal(id?: string) {
  state.dataId = id ?? null
  state.formModel = { ...defaultFormData }
  state.showModal = true
  if (id) {
    await fetchDetail(id)
  }
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const data = (await msgFeedbackApi.detail({ id })).data ?? {}
    state.formModel = { ...defaultFormData, ...data }
  } finally {
    state.loading = false
  }
}

function closeModal() {
  state.showModal = false
  state.submitLoading = false
}

async function submitForm() {
  await formRef.value?.validate()
  state.submitLoading = true
  try {
    await msgFeedbackApi.update({
      id: state.dataId,
      status: state.formModel.status,
      reply: state.formModel.reply || null,
    })
    window.$message.success('更新成功')
    emit('saved')
    closeModal()
  } finally {
    state.submitLoading = false
  }
}

defineExpose({ openModal })
</script>

<template>
  <NModal
    v-model:show="state.showModal"
    preset="card"
    draggable
    :mask-closable="false"
    :title="modalTitle"
    style="width: min(520px, 94vw)"
    :segmented="{ content: true, action: true }"
  >
    <NSpin :show="state.loading">
      <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
        <NForm
          ref="formRef"
          :model="state.formModel"
          :rules="rules"
          label-placement="left"
          label-width="100"
          :disabled="state.loading || state.submitLoading"
        >
          <NFormItem label="状态" path="status">
            <DictSelect v-model="state.formModel.status" dict-code="FEEDBACK_STATUS" type="radio" />
          </NFormItem>
          <NFormItem label="管理员回复" path="reply">
            <NInput
              v-model:value="state.formModel.reply"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 8 }"
              placeholder="输入回复内容（可选）"
            />
          </NFormItem>
        </NForm>
      </NScrollbar>
    </NSpin>
    <template #action>
      <NSpace justify="end">
        <NButton @click="closeModal"> 取消 </NButton>
        <NButton type="primary" :loading="state.submitLoading" @click="submitForm"> 确认 </NButton>
      </NSpace>
    </template>
  </NModal>
</template>
