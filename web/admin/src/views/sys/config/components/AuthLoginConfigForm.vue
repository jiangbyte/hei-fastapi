<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const fields = reactive({
  failureWindow: { id: '', value: 0, remark: '' },
  accountMaxFailures: { id: '', value: 0, remark: '' },
  ipMaxFailures: { id: '', value: 0, remark: '' },
  lockSeconds: { id: '', value: 0, remark: '' },
  saving: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of res.data ?? []) {
    if (row.config_key === 'auth.login_failure_window_seconds')
      fields.failureWindow = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
    else if (row.config_key === 'auth.login_account_max_failures')
      fields.accountMaxFailures = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
    else if (row.config_key === 'auth.login_ip_max_failures')
      fields.ipMaxFailures = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
    else if (row.config_key === 'auth.login_lock_seconds')
      fields.lockSeconds = {
        id: row.id,
        value: Number(row.config_value) || 0,
        remark: row.remark ?? '',
      }
  }
})

async function saveAll() {
  fields.saving = true
  try {
    await configApi.batchSave({
      items: [
        {
          id: fields.failureWindow.id,
          config_key: 'auth.login_failure_window_seconds',
          config_value: String(fields.failureWindow.value),
        },
        {
          id: fields.accountMaxFailures.id,
          config_key: 'auth.login_account_max_failures',
          config_value: String(fields.accountMaxFailures.value),
        },
        {
          id: fields.ipMaxFailures.id,
          config_key: 'auth.login_ip_max_failures',
          config_value: String(fields.ipMaxFailures.value),
        },
        {
          id: fields.lockSeconds.id,
          config_key: 'auth.login_lock_seconds',
          config_value: String(fields.lockSeconds.value),
        },
      ],
    })
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
        <NFormItem label="登录失败统计窗口" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.failureWindow.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.failureWindow.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="单账号最大失败次数" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.accountMaxFailures.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.accountMaxFailures.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="单 IP 最大失败次数" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.ipMaxFailures.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.ipMaxFailures.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="登录锁定时间" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.lockSeconds.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.lockSeconds.remark }}
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
