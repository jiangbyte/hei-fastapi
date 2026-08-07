<!-- Author: Charlie -->

<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import ImageUpload from '@/components/upload/ImageUpload.vue'
import { bannerApi } from '@/api'
import { createRequiredRule, formatDateTime, toApiDateTime, toNullableString } from '@/utils'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits<{
  saved: []
}>()

const formRef = ref<FormInst | null>(null)
const defaultFormData = {
  title: '',
  image: '',
  url: '',
  link_type: 'URL',
  summary: '',
  description: '',
  category: 'HOME',
  type: 'CAROUSEL',
  position: 'HOME_TOP',
  display_scope: 'PORTAL',
  sort: 0,
  status: 'ENABLED',
  dateRange: null,
}
const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  dataId: null as string | null,
  formModel: { ...defaultFormData },
})

const modalTitle = computed(() => (state.dataId ? '编辑展示图' : '新增展示图'))

const rules = computed<FormRules>(() => ({
  title: createRequiredRule('标题', 'input'),
  image: createRequiredRule('图片', 'input'),
  link_type: createRequiredRule('链接类型', 'change'),
  category: createRequiredRule('分类', 'change'),
  type: createRequiredRule('类型', 'change'),
  position: createRequiredRule('岗位', 'change'),
  display_scope: createRequiredRule('展示范围', 'change'),
  status: createRequiredRule('状态', 'change'),
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
    const response = await bannerApi.detail({ id })
    const startStr = response.data?.start_at ? formatDateTime(response.data.start_at, '') : null
    const endStr = response.data?.end_at ? formatDateTime(response.data.end_at, '') : null
    state.formModel = Object.assign({}, defaultFormData, response.data, {
      dateRange: startStr && endStr ? [startStr, endStr] : null,
    })
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
    const payload = {
      ...state.formModel,
      url: toNullableString(state.formModel.url),
      summary: toNullableString(state.formModel.summary),
      description: toNullableString(state.formModel.description),
      sort: Number(state.formModel.sort ?? 0),
      start_at: state.formModel.dateRange?.[0] ? toApiDateTime(state.formModel.dateRange[0]) : null,
      end_at: state.formModel.dateRange?.[1] ? toApiDateTime(state.formModel.dateRange[1]) : null,
    }

    if (state.dataId) {
      await bannerApi.update({
        ...payload,
        id: state.dataId,
      })
      window.$message.success('更新成功')
    } else {
      await bannerApi.create(payload)
      window.$message.success('创建成功')
    }

    closeModal()
    emit('saved')
  } finally {
    state.submitLoading = false
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
    :title="modalTitle"
    style="width: 720px"
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
          <NFormItem :label="'标题'" path="title">
            <NInput v-model:value="state.formModel.title" />
          </NFormItem>
          <NFormItem :label="'图片'" path="image">
            <ImageUpload v-model:value="state.formModel.image" />
          </NFormItem>
          <NFormItem :label="'目标URL'" path="url">
            <NInput v-model:value="state.formModel.url" />
          </NFormItem>
          <NFormItem :label="'链接类型'" path="link_type">
            <DictSelect
              v-model="state.formModel.link_type"
              dict-code="BANNER_LINK_TYPE"
              type="radio"
            />
          </NFormItem>
          <NFormItem :label="'分类'" path="category">
            <DictSelect v-model="state.formModel.category" dict-code="BANNER_CATEGORY" />
          </NFormItem>
          <NFormItem :label="'类型'" path="type">
            <DictSelect v-model="state.formModel.type" dict-code="BANNER_TYPE" />
          </NFormItem>
          <NFormItem :label="'岗位'" path="position">
            <DictSelect v-model="state.formModel.position" dict-code="BANNER_POSITION" />
          </NFormItem>
          <NFormItem :label="'展示范围'" path="display_scope">
            <DictSelect v-model="state.formModel.display_scope" dict-code="BANNER_DISPLAY_SCOPE" />
          </NFormItem>
          <NFormItem :label="'排序'" path="sort">
            <NInputNumber v-model:value="state.formModel.sort" class="w-full" :min="0" />
          </NFormItem>
          <NFormItem :label="'状态'" path="status">
            <DictSelect v-model="state.formModel.status" dict-code="COMMON_STATUS" type="radio" />
          </NFormItem>
          <NFormItem :label="'展示时间'" path="dateRange">
            <NDatePicker
              v-model:formatted-value="state.formModel.dateRange"
              type="datetimerange"
              clearable
              value-format="yyyy-MM-dd HH:mm:ss"
              class="w-full"
            />
          </NFormItem>
          <NFormItem :label="'摘要'" path="summary">
            <NInput v-model:value="state.formModel.summary" />
          </NFormItem>
          <NFormItem :label="'描述'" path="description">
            <NInput
              v-model:value="state.formModel.description"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
            />
          </NFormItem>
        </NForm>
      </NScrollbar>
    </NSpin>

    <template #action>
      <NSpace justify="end" align="center">
        <NButton @click="closeModal"> 取消 </NButton>
        <NButton type="primary" :loading="state.submitLoading" @click="submitForm"> 确认 </NButton>
      </NSpace>
    </template>
  </NModal>
</template>
