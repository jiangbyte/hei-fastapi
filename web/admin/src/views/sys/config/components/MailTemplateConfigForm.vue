<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { useMessage } from 'naive-ui'
import { onMounted, reactive, ref, computed } from 'vue'

interface TemplateItem {
  id: string
  config_key: string
  value: string
  remark: string
}

interface TabState {
  type: string
  label: string
  subject: TemplateItem
  body: TemplateItem
  saving: boolean
}

const emit = defineEmits<{ saved: [] }>()
const message = useMessage()
const loading = ref(false)

const tabs: TabState[] = reactive([
  {
    type: 'forgot_password',
    label: '忘记密码邮件',
    subject: { id: '', config_key: 'mail.template.forgot_password.subject', value: '', remark: '' },
    body: { id: '', config_key: 'mail.template.forgot_password.body', value: '', remark: '' },
    saving: false,
  },
])

const activeTab = reactive({ value: 'forgot_password' as string })

const currentTab = computed(() => tabs.find((t) => t.type === activeTab.value) ?? tabs[0])

onMounted(async () => {
  loading.value = true
  try {
    const res = await configApi.list({ category: 'MAIL_TEMPLATE' })
    const all = (res.data ?? []) as any[]
    for (const tab of tabs) {
      const subjectRow = all.find((r: any) => r.config_key === tab.subject.config_key)
      const bodyRow = all.find((r: any) => r.config_key === tab.body.config_key)
      if (subjectRow) {
        tab.subject = {
          ...tab.subject,
          id: subjectRow.id,
          value: subjectRow.config_value ?? '',
          remark: subjectRow.remark ?? '',
        }
      }
      if (bodyRow) {
        tab.body = {
          ...tab.body,
          id: bodyRow.id,
          value: bodyRow.config_value ?? '',
          remark: bodyRow.remark ?? '',
        }
      }
    }
  } finally {
    loading.value = false
  }
})

async function saveCurrent() {
  const tab = currentTab.value
  tab.saving = true
  try {
    const items = [
      { id: tab.subject.id, config_key: tab.subject.config_key, config_value: tab.subject.value },
      { id: tab.body.id, config_key: tab.body.config_key, config_value: tab.body.value },
    ]
    await configApi.batchSave({ items })
    message.success('保存成功')
    await refreshTab()
    emit('saved')
  } finally {
    tab.saving = false
  }
}

async function refreshTab() {
  const res = await configApi.list({ category: 'MAIL_TEMPLATE' })
  const all = (res.data ?? []) as any[]
  for (const tab of tabs) {
    const subjectRow = all.find((r: any) => r.config_key === tab.subject.config_key)
    const bodyRow = all.find((r: any) => r.config_key === tab.body.config_key)
    if (subjectRow)
      tab.subject = {
        ...tab.subject,
        id: subjectRow.id,
        value: subjectRow.config_value ?? '',
        remark: subjectRow.remark ?? '',
      }
    if (bodyRow)
      tab.body = {
        ...tab.body,
        id: bodyRow.id,
        value: bodyRow.config_value ?? '',
        remark: bodyRow.remark ?? '',
      }
  }
}
</script>

<template>
  <NSpin :show="loading">
    <div class="mail-template-wrapper">
      <NTabs
        v-model:value="activeTab.value"
        type="card"
        placement="left"
        animated
        :style="{ minHeight: '420px' }"
      >
        <NTabPane v-for="tab in tabs" :key="tab.type" :name="tab.type" :tab="tab.label">
          <div class="form-area">
            <div class="form-actions">
              <NButton type="primary" size="small" :loading="tab.saving" @click="saveCurrent">
                保存
              </NButton>
            </div>

            <NForm label-placement="top" class="mt-16px">
              <NFormItem label="邮件主题">
                <NInput v-model:value="tab.subject.value" placeholder="如：{{app_name}} 密码重置" />
              </NFormItem>
              <NFormItem label="邮件正文">
                <NInput
                  v-model:value="tab.body.value"
                  type="textarea"
                  :autosize="{ minRows: 6, maxRows: 16 }"
                  placeholder="邮件正文模板，支持变量占位符"
                />
              </NFormItem>
            </NForm>

            <NAlert type="info" :bordered="false" class="mt-16px">
              <template #header> 可用变量 </template>
              <ul class="var-list">
                <li>
                  <code v-pre>{{ app_name }}</code> — 应用名称
                </li>
                <li>
                  <code v-pre>{{ reset_link }}</code> — 重置密码链接
                </li>
                <li>
                  <code v-pre>{{ email }}</code> — 用户邮箱
                </li>
                <li>
                  <code v-pre>{{ expire_minutes }}</code> — 链接有效分钟数
                </li>
              </ul>
            </NAlert>
          </div>
        </NTabPane>
      </NTabs>
    </div>
  </NSpin>
</template>

<style scoped>
.mail-template-wrapper {
  min-height: 400px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}
:deep(.n-tabs-tab) {
  min-width: 120px;
}
.mt-16px {
  margin-top: 16px;
}
.var-list {
  margin: 4px 0 0;
  padding-left: 20px;
  line-height: 1.8;
}
.var-list code {
  font-size: 13px;
  background: var(--n-color, #f5f5f5);
  padding: 1px 6px;
  border-radius: 3px;
}
</style>
