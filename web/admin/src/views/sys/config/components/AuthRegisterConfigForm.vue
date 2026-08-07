<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

interface BoolItem {
  id: string
  config_key: string
  remark: string
  value: boolean
}

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const fields = reactive({
  portalEnabled: { id: '', value: false, remark: '' } as BoolItem,
  saving: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of res.data ?? []) {
    if (row.config_key === 'auth.portal_register_enabled')
      fields.portalEnabled = {
        id: row.id,
        config_key: row.config_key,
        value: row.config_value === 'true',
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
          id: fields.portalEnabled.id,
          config_key: 'auth.portal_register_enabled',
          config_value: String(fields.portalEnabled.value),
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
        <NFormItem label="门户端注册" :style="{ marginBottom: 0 }">
          <div>
            <NSwitch v-model:value="fields.portalEnabled.value" />
            <div class="hint">
              {{ fields.portalEnabled.remark }}
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
