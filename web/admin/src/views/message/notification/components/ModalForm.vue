<!--
  Author: Charlie

  通知表单：支持多选范围。
-->
<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import { msgNotificationApi } from '@/api'
import { createRequiredRule, formatDateTime } from '@/utils'
import { MdEditor, RichTextEditor } from '@/components/editor'
import UserSelector from '@/components/selector/UserSelector.vue'
import DeptSelector from '@/components/selector/DeptSelector.vue'
import RoleSelector from '@/components/selector/RoleSelector.vue'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits<{ saved: [] }>()

const formRef = ref<FormInst | null>(null)
const defaultFormData: Record<string, any> = {
  title: '',
  content: '',
  content_type: 'text',
  category: '',
  severity: 'info',
  target_scope: 'ALL',
  target_account_types: [],
  target_account_ids: [],
  target_dept_ids: [],
  target_role_ids: [],
  status: 'ENABLED',
  publish_at: null,
}
const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  dataId: null as string | null,
  formModel: normalizeFormData(),
  showUserSelector: false,
  showDeptSelector: false,
  showRoleSelector: false,
  userNames: [] as string[],
  deptNames: [] as string[],
  roleNames: [] as string[],
})

const modalTitle = computed(() => (state.dataId ? '编辑通知' : '新增通知'))
const rules = computed<FormRules>(() => ({
  title: [createRequiredRule('标题', 'input')],
  content: [createRequiredRule('内容', 'input')],
  content_type: [createRequiredRule('内容格式', 'change')],
  category: [createRequiredRule('分类', 'change')],
  severity: [createRequiredRule('等级', 'change')],
  target_scope: [createRequiredRule('目标范围', 'change')],
  status: [createRequiredRule('状态', 'change')],
}))

async function openModal(id?: string, defaults: Partial<typeof defaultFormData> = {}) {
  state.dataId = id ?? null
  state.formModel = normalizeFormData(defaults)
  state.userNames = []
  state.deptNames = []
  state.roleNames = []
  state.showModal = true
  if (id) {
    await fetchDetail(id)
  }
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const data = (await msgNotificationApi.detail({ id })).data ?? {}
    state.formModel = normalizeFormData(data)
    state.userNames = data.target_account_ids?.length
      ? data.target_account_ids.map(() => '已选中')
      : []
  } finally {
    state.loading = false
  }
}

function normalizeFormData(data: Record<string, any> = {}) {
  return { ...defaultFormData, ...data, publish_at: formatDateTime(data.publish_at, '') || null }
}

function normalizeSubmitData(data: Record<string, any>) {
  const r = { ...data }
  r.publish_at = ((v) => {
    const t = formatDateTime(v, '')
    if (!t) return null
    const d = new Date(t.replace(' ', 'T') + '+08:00')
    return Number.isNaN(d.getTime()) ? null : d.toISOString().replace(/\.\d{3}Z$/, 'Z')
  })(data.publish_at)
  // 移除隐藏且自动设置的字段
  delete r.sender_account_type
  delete r.sender_account_id
  delete r.source_type
  delete r.source_id
  delete r.revoked_at
  r.extra = {}
  // 确保为数组
  if (!Array.isArray(r.target_account_types)) r.target_account_types = []
  if (!Array.isArray(r.target_account_ids)) r.target_account_ids = []
  if (!Array.isArray(r.target_dept_ids)) r.target_dept_ids = []
  if (!Array.isArray(r.target_role_ids)) r.target_role_ids = []
  return r
}

function closeModal() {
  state.showModal = false
  state.submitLoading = false
}

async function submitForm() {
  await formRef.value?.validate()
  state.submitLoading = true
  try {
    const payload = normalizeSubmitData(state.formModel)
    if (state.dataId) {
      await msgNotificationApi.update({ ...payload, id: state.dataId })
      window.$message.success('更新成功')
    } else {
      await msgNotificationApi.create(payload)
      window.$message.success('创建成功')
    }
    emit('saved')
    closeModal()
  } finally {
    state.submitLoading = false
  }
}

function handleUserSelect(account: { id: string; name: string }) {
  state.formModel.target_account_ids = [account.id]
  state.userNames = [account.name]
  state.showUserSelector = false
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
    style="width: min(780px, 94vw)"
    :segmented="{ content: true, action: true }"
  >
    <NSpin :show="state.loading">
      <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
        <NForm
          ref="formRef"
          :model="state.formModel"
          :rules="rules"
          label-placement="left"
          label-width="110"
          :disabled="state.loading || state.submitLoading"
        >
          <NGrid :cols="2" :x-gap="16">
            <NGi>
              <NFormItem label="标题" path="title">
                <NInput v-model:value="state.formModel.title" />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="内容格式" path="content_type">
                <DictSelect v-model="state.formModel.content_type" dict-code="CONTENT_TYPE" />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="分类" path="category">
                <DictSelect v-model="state.formModel.category" dict-code="SYS_BIZ_CATEGORY" />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="等级" path="severity">
                <DictSelect v-model="state.formModel.severity" dict-code="NOTIFICATION_SEVERITY" />
              </NFormItem>
            </NGi>
            <NGi :span="2">
              <NFormItem label="目标范围" path="target_scope">
                <DictSelect
                  v-model="state.formModel.target_scope"
                  dict-code="TARGET_SCOPE"
                  type="radio"
                />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="目标账户类型" path="target_account_types">
                <DictSelect
                  v-model="state.formModel.target_account_types"
                  dict-code="ACCOUNT_TYPE"
                  type="checkbox"
                />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="状态" path="status">
                <DictSelect
                  v-model="state.formModel.status"
                  dict-code="PUBLISH_STATUS"
                  type="radio"
                />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="发布时间" path="publish_at">
                <NDatePicker
                  v-model:formatted-value="state.formModel.publish_at"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  class="w-full"
                  clearable
                />
              </NFormItem>
            </NGi>

            <!-- 按范围的选择器 -->
            <NGi v-if="state.formModel.target_scope === 'SPECIFIC'">
              <NFormItem label="目标用户" path="target_account_ids">
                <NInput
                  :value="state.userNames.join(', ') || ''"
                  readonly
                  placeholder="点击选择用户"
                >
                  <template #suffix>
                    <NButton
                      text
                      type="primary"
                      size="small"
                      @click="state.showUserSelector = true"
                    >
                      选择
                    </NButton>
                  </template>
                </NInput>
              </NFormItem>
            </NGi>
            <NGi v-if="state.formModel.target_scope === 'DEPARTMENT'">
              <NFormItem label="目标部门" path="target_dept_ids">
                <NInput
                  :value="state.deptNames.join(', ') || ''"
                  readonly
                  placeholder="点击选择部门"
                >
                  <template #suffix>
                    <NButton
                      text
                      type="primary"
                      size="small"
                      @click="state.showDeptSelector = true"
                    >
                      选择
                    </NButton>
                  </template>
                </NInput>
              </NFormItem>
            </NGi>
            <NGi v-if="state.formModel.target_scope === 'ROLE'">
              <NFormItem label="目标角色" path="target_role_ids">
                <NInput
                  :value="state.roleNames.join(', ') || ''"
                  readonly
                  placeholder="点击选择角色"
                >
                  <template #suffix>
                    <NButton
                      text
                      type="primary"
                      size="small"
                      @click="state.showRoleSelector = true"
                    >
                      选择
                    </NButton>
                  </template>
                </NInput>
              </NFormItem>
            </NGi>
          </NGrid>

          <NFormItem label="内容" path="content">
            <div v-if="state.formModel.content_type === 'text'" class="w-full">
              <NInput
                v-model:value="state.formModel.content"
                type="textarea"
                :autosize="{ minRows: 5, maxRows: 15 }"
              />
            </div>
            <MdEditor
              v-else-if="state.formModel.content_type === 'markdown'"
              v-model:value="state.formModel.content"
              :height="400"
            />
            <RichTextEditor v-else v-model:value="state.formModel.content" :height="400" />
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

  <UserSelector v-model:visible="state.showUserSelector" mode="single" @select="handleUserSelect" />
  <DeptSelector
    v-model:visible="state.showDeptSelector"
    mode="single"
    @select="
      (v) => {
        state.formModel.target_dept_ids = [v.id]
        state.deptNames = [v.name]
        state.showDeptSelector = false
      }
    "
  />
  <RoleSelector
    v-model:visible="state.showRoleSelector"
    mode="single"
    @select="
      (v) => {
        state.formModel.target_role_ids = [v.id]
        state.roleNames = [v.name]
        state.showRoleSelector = false
      }
    "
  />
</template>
