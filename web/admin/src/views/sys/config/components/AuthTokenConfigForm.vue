<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const state = reactive({
  tokenTtl: { id: '', value: 0, remark: '' },
  resetTtl: { id: '', value: 0, remark: '' },
  saving: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of res.data ?? []) {
    if (row.config_key === 'auth.token_ttl_seconds')
      state.tokenTtl = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
    else if (row.config_key === 'auth.password_reset_token_ttl_seconds')
      state.resetTtl = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
  }
})

async function saveAll() {
  state.saving = true
  try {
    await configApi.batchSave({
      items: [
        {
          id: state.tokenTtl.id,
          config_key: 'auth.token_ttl_seconds',
          config_value: String(state.tokenTtl.value),
        },
        {
          id: state.resetTtl.id,
          config_key: 'auth.password_reset_token_ttl_seconds',
          config_value: String(state.resetTtl.value),
        },
      ],
    })
    window.$message.success('保存成功')
    emit('saved')
  } finally {
    state.saving = false
  }
}
</script>

<template>
  <NForm label-placement="top" :label-width="140">
    <NGrid :cols="24" :x-gap="24" :y-gap="12">
      <NGi :span="12">
        <NFormItem label="会话 Token 过期时间" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="state.tokenTtl.value" class="w-full" :min="0" />
            <div class="hint">
              {{ state.tokenTtl.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="密码重置 Token 有效期" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="state.resetTtl.value" class="w-full" :min="0" />
            <div class="hint">
              {{ state.resetTtl.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
    </NGrid>
    <NButton type="primary" class="mt-16px" :loading="state.saving" @click="saveAll">
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
