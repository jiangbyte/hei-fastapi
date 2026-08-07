<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const fields = reactive({
  maxBytes: { id: '', value: 0, remark: '' },
  presignExpire: { id: '', value: 0, remark: '' },
  categoryMaxLength: { id: '', value: 0, remark: '' },
  allowedContentTypes: { id: '', tags: [] as string[], remark: '' },
  allowedExtensions: { id: '', tags: [] as string[], remark: '' },
  deniedExtensions: { id: '', tags: [] as string[], remark: '' },
  saving: false,
})

function parseTags(raw: string | null | undefined): string[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : [raw]
  } catch {
    return []
  }
}

function tagsToJson(tags: string[]): string {
  return JSON.stringify(tags)
}

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of res.data ?? []) {
    switch (row.config_key) {
      case 'storage.upload_max_bytes':
        fields.maxBytes = {
          id: row.id,
          value: Number(row.config_value) || 0,
          remark: row.remark ?? '',
        }
        break
      case 'storage.presign_expire_seconds':
        fields.presignExpire = {
          id: row.id,
          value: Number(row.config_value) || 0,
          remark: row.remark ?? '',
        }
        break
      case 'storage.upload_category_max_length':
        fields.categoryMaxLength = {
          id: row.id,
          value: Number(row.config_value) || 0,
          remark: row.remark ?? '',
        }
        break
      case 'storage.upload_allowed_content_types':
        fields.allowedContentTypes = {
          id: row.id,
          tags: parseTags(row.config_value),
          remark: row.remark ?? '',
        }
        break
      case 'storage.upload_allowed_extensions':
        fields.allowedExtensions = {
          id: row.id,
          tags: parseTags(row.config_value),
          remark: row.remark ?? '',
        }
        break
      case 'storage.upload_denied_extensions':
        fields.deniedExtensions = {
          id: row.id,
          tags: parseTags(row.config_value),
          remark: row.remark ?? '',
        }
        break
    }
  }
})

function buildPayload() {
  return {
    items: [
      {
        id: fields.maxBytes.id,
        config_key: 'storage.upload_max_bytes',
        config_value: String(fields.maxBytes.value),
      },
      {
        id: fields.presignExpire.id,
        config_key: 'storage.presign_expire_seconds',
        config_value: String(fields.presignExpire.value),
      },
      {
        id: fields.categoryMaxLength.id,
        config_key: 'storage.upload_category_max_length',
        config_value: String(fields.categoryMaxLength.value),
      },
      {
        id: fields.allowedContentTypes.id,
        config_key: 'storage.upload_allowed_content_types',
        config_value: tagsToJson(fields.allowedContentTypes.tags),
      },
      {
        id: fields.allowedExtensions.id,
        config_key: 'storage.upload_allowed_extensions',
        config_value: tagsToJson(fields.allowedExtensions.tags),
      },
      {
        id: fields.deniedExtensions.id,
        config_key: 'storage.upload_denied_extensions',
        config_value: tagsToJson(fields.deniedExtensions.tags),
      },
    ],
  }
}

async function saveAll() {
  fields.saving = true
  try {
    await configApi.batchSave(buildPayload())
    window.$message.success('保存成功')
    emit('saved')
  } finally {
    fields.saving = false
  }
}
</script>

<template>
  <NForm label-placement="top" :label-width="140">
    <NGrid :cols="24" :x-gap="24" :y-gap="12">
      <NGi :span="12">
        <NFormItem label="上传大小上限" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.maxBytes.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.maxBytes.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="预签名 URL 有效期" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.presignExpire.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.presignExpire.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="分类名最大长度" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.categoryMaxLength.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.categoryMaxLength.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="24">
        <NFormItem label="允许的 MIME 类型" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NDynamicTags v-model:value="fields.allowedContentTypes.tags" :max="100" />
            <div class="hint">
              {{ fields.allowedContentTypes.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="24">
        <NFormItem label="允许的文件扩展名" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NDynamicTags v-model:value="fields.allowedExtensions.tags" :max="100" />
            <div class="hint">
              {{ fields.allowedExtensions.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="24">
        <NFormItem label="禁止的扩展名" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NDynamicTags v-model:value="fields.deniedExtensions.tags" :max="100" />
            <div class="hint">
              {{ fields.deniedExtensions.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
    </NGrid>
    <NButton type="primary" class="mt-16px" :loading="fields.saving" @click="saveAll">
      保存配置
    </NButton>
  </NForm>
</template>

<style scoped>
.hint {
  font-size: 12px;
  color: #aaa;
  margin-top: 2px;
}
</style>
