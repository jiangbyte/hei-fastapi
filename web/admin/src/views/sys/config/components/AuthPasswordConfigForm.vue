<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const field = reactive({
  id: '',
  value: '',
  remark: '',
  saving: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  const row = (res.data ?? [])[0]
  if (row) {
    field.id = row.id
    field.value = row.config_value ?? ''
    field.remark = row.remark ?? ''
  }
})

async function saveAll() {
  field.saving = true
  try {
    await configApi.batchSave({
      items: [{ id: field.id, config_key: 'auth.default_password', config_value: field.value }],
    })
    window.$message.success('保存成功')
    emit('saved')
  } finally {
    field.saving = false
  }
}
</script>

<template>
  <NForm label-placement="top" :label-width="140">
    <NGrid :cols="24" :x-gap="24" :y-gap="12">
      <NGi :span="8">
        <NFormItem label="默认密码" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput v-model:value="field.value" type="password" show-password-on="click" />
            <div class="hint">
              {{ field.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
    </NGrid>
    <NButton type="primary" class="mt-16px" :loading="field.saving" @click="saveAll">
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
