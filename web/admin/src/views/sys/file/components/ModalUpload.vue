<!-- Author: Charlie -->

<script setup lang="ts">
import type { UploadFileInfo } from 'naive-ui'
import { fileApi } from '@/api'
import { computed, onBeforeUnmount, onMounted, reactive } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { Icon } from '@iconify/vue/offline'
import { dictList } from '@/utils/dict'

const emit = defineEmits<{
  saved: []
  uploaded: [file: any]
}>()

const fallbackStorageProviderOptions = [
  { label: '本地存储', value: 'local' },
  { label: 'MinIO', value: 'minio' },
  { label: 'Amazon S3', value: 's3' },
  { label: '阿里云 OSS', value: 'oss' },
]

const storageProviderOptions = computed(() => {
  const options = dictList('STORAGE_PROVIDER')
  return options.length ? options : fallbackStorageProviderOptions
})

const defaultStorageProvider = computed(() =>
  String(storageProviderOptions.value[0]?.value || 'local'),
)

const state = reactive({
  showModal: false,
  submitLoading: false,
  storageProvider: '',
  uploadFileList: [] as UploadFileInfo[],
  succeeded: 0,
  failed: 0,
})

function openModal() {
  resetForm()
  state.showModal = true
}

function resetForm() {
  state.storageProvider = defaultStorageProvider.value
  state.uploadFileList = []
  state.succeeded = 0
  state.failed = 0
}

function handleUpdateShow(show: boolean) {
  if (show) {
    state.showModal = true
    return
  }
  closeModal()
}

function closeModal() {
  if (state.submitLoading) {
    window.$message.warning('文件正在上传，请等待上传完成')
    return
  }
  state.showModal = false
}

async function submitForm() {
  const pending = state.uploadFileList.filter((f) => f.status === 'pending' || f.status === 'error')
  if (!pending.length) {
    window.$message.warning('请先选择文件')
    return
  }
  state.submitLoading = true
  state.succeeded = 0
  state.failed = 0
  try {
    for (const fileInfo of pending) {
      const file = fileInfo.file
      if (!file) continue
      fileInfo.status = 'uploading'
      try {
        await fileApi.upload(file, {
          storage_provider: state.storageProvider,
        })
        fileInfo.status = 'finished'
        fileInfo.percentage = 100
        state.succeeded++
      } catch {
        fileInfo.status = 'error'
        state.failed++
      }
    }
    if (state.succeeded > 0) {
      window.$message.success(
        `上传完成：成功 ${state.succeeded} 个${state.failed > 0 ? `，失败 ${state.failed} 个` : ''}`,
      )
      emit('saved')
      if (state.failed === 0) {
        state.showModal = false
      }
    } else {
      window.$message.error('上传失败')
    }
  } finally {
    state.submitLoading = false
  }
}

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (!state.submitLoading) {
    return
  }
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave(() => {
  if (!state.submitLoading) {
    return true
  }
  return window.confirm('文件正在上传，离开页面将中断上传，确认离开?')
})

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

defineExpose({
  openModal,
})
</script>

<template>
  <NModal
    :show="state.showModal"
    preset="card"
    draggable
    :mask-closable="false"
    :close-on-esc="!state.submitLoading"
    :closable="!state.submitLoading"
    :title="'上传文件'"
    style="width: 560px"
    :segmented="{ content: true, action: true }"
    @update:show="handleUpdateShow"
  >
    <NForm label-placement="left" label-width="110" :disabled="state.submitLoading">
      <NFormItem :label="'存储提供商'">
        <NSelect
          v-model:value="state.storageProvider"
          :options="storageProviderOptions"
          :disabled="state.submitLoading"
        />
      </NFormItem>
      <NFormItem :label="'选择文件'">
        <NUpload
          class="w-full"
          multiple
          :default-upload="false"
          :disabled="state.submitLoading"
          :file-list="state.uploadFileList"
          :show-cancel-button="!state.submitLoading"
          :show-retry-button="false"
          @update:file-list="state.uploadFileList = $event"
        >
          <NUploadDragger>
            <div class="upload-dragger">
              <NIcon size="28">
                <Icon icon="icon-park-outline:upload" />
              </NIcon>
              <div>点击或拖拽文件到此处</div>
            </div>
          </NUploadDragger>
        </NUpload>
      </NFormItem>
    </NForm>

    <template #action>
      <NSpace justify="end" align="center">
        <NButton :disabled="state.submitLoading" @click="closeModal"> 取消 </NButton>
        <NButton type="primary" :loading="state.submitLoading" @click="submitForm">
          {{
            state.submitLoading
              ? `上传中 ${state.succeeded + state.failed}/${state.uploadFileList.length}`
              : '确认上传'
          }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.upload-dragger {
  display: grid;
  justify-items: center;
  gap: 6px;
  padding: 24px 0;
  color: var(--text-color-3);
}
</style>
