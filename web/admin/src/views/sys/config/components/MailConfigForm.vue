<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

interface Item {
  id: string
  value: string
  remark: string
}

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const fields = reactive({
  host: { id: '', value: '', remark: '' } as Item,
  port: { id: '', value: 0, remark: '' },
  username: { id: '', value: '', remark: '' } as Item,
  password: { id: '', value: '', remark: '' } as Item,
  fromEmail: { id: '', value: '', remark: '' } as Item,
  fromName: { id: '', value: '', remark: '' } as Item,
  useTls: { id: '', value: false, remark: '' },
  saving: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of res.data ?? []) {
    switch (row.config_key) {
      case 'mail.host':
        fields.host = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'mail.port':
        fields.port = { id: row.id, value: Number(row.config_value) || 0, remark: row.remark ?? '' }
        break
      case 'mail.username':
        fields.username = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'mail.password':
        fields.password = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'mail.from_email':
        fields.fromEmail = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'mail.from_name':
        fields.fromName = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'mail.use_tls':
        fields.useTls = { id: row.id, value: row.config_value === 'true', remark: row.remark ?? '' }
        break
    }
  }
})

function buildPayload() {
  return {
    items: [
      { id: fields.host.id, config_key: 'mail.host', config_value: fields.host.value },
      { id: fields.port.id, config_key: 'mail.port', config_value: String(fields.port.value) },
      { id: fields.username.id, config_key: 'mail.username', config_value: fields.username.value },
      { id: fields.password.id, config_key: 'mail.password', config_value: fields.password.value },
      {
        id: fields.fromEmail.id,
        config_key: 'mail.from_email',
        config_value: fields.fromEmail.value,
      },
      { id: fields.fromName.id, config_key: 'mail.from_name', config_value: fields.fromName.value },
      {
        id: fields.useTls.id,
        config_key: 'mail.use_tls',
        config_value: String(fields.useTls.value),
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
      <NGi :span="16">
        <NFormItem label="SMTP 地址" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput v-model:value="fields.host.value" />
            <div class="hint">
              {{ fields.host.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="8">
        <NFormItem label="SMTP 端口" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInputNumber v-model:value="fields.port.value" class="w-full" :min="0" />
            <div class="hint">
              {{ fields.port.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="SMTP 用户名" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput v-model:value="fields.username.value" />
            <div class="hint">
              {{ fields.username.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="SMTP 密码" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput
              v-model:value="fields.password.value"
              type="password"
              show-password-on="click"
            />
            <div class="hint">
              {{ fields.password.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="发件人邮箱" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput v-model:value="fields.fromEmail.value" />
            <div class="hint">
              {{ fields.fromEmail.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="12">
        <NFormItem label="发件人名称" :style="{ marginBottom: 0 }">
          <div class="w-full">
            <NInput v-model:value="fields.fromName.value" />
            <div class="hint">
              {{ fields.fromName.remark }}
            </div>
          </div>
        </NFormItem>
      </NGi>
      <NGi :span="8">
        <NFormItem label="TLS 加密" :style="{ marginBottom: 0 }">
          <div>
            <NSwitch v-model:value="fields.useTls.value" />
            <div class="hint">
              {{ fields.useTls.remark }}
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
