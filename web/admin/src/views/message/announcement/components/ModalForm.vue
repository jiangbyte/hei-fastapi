<!--
  Author: Charlie

  公告表单：支持多选范围与发布位置。
-->
<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import { msgAnnouncementApi } from '@/api'
import { createRequiredRule, dictList, formatDateTime } from '@/utils'
import { MdEditor, RichTextEditor } from '@/components/editor'
import UserSelector from '@/components/selector/UserSelector.vue'
import DeptSelector from '@/components/selector/DeptSelector.vue'
import RoleSelector from '@/components/selector/RoleSelector.vue'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits<{ saved: [] }>()

const formRef = ref<FormInst | null>(null)
const locationOptions = computed(() => dictList('NOTIFY_LOCATION'))
const defaultFormData: Record<string, any> = {
  title: '',
  content: '',
  content_type: 'text',
  severity: 'info',
  target_scope: 'ALL',
  target_account_types: [],
  target_account_ids: [],
  target_dept_ids: [],
  target_role_ids: [],
  publish_locations: {},
  is_pinned: false,
  pinned_until: null,
  status: 'ENABLED',
  publish_at: null,
  expire_at: null,
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

const modalTitle = computed(() => (state.dataId ? '编辑公告' : '新增公告'))
const rules = computed<FormRules>(() => ({
  title: [createRequiredRule('标题', 'input')],
  content: [createRequiredRule('内容', 'input')],
  content_type: [createRequiredRule('内容格式', 'change')],
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
    const data = (await msgAnnouncementApi.detail({ id })).data ?? {}
    state.formModel = normalizeFormData(data)
    state.userNames = data.target_account_ids?.length
      ? data.target_account_ids.map(() => '已选中')
      : []
  } finally {
    state.loading = false
  }
}

function normalizeFormData(data: Record<string, any> = {}) {
  return {
    ...defaultFormData,
    ...data,
    pinned_until: formatDateTime(data.pinned_until, '') || null,
    publish_at: formatDateTime(data.publish_at, '') || null,
    expire_at: formatDateTime(data.expire_at, '') || null,
  }
}

function normalizeSubmitData(data: Record<string, any>) {
  const r = { ...data }
  const n = (v: unknown) => {
    const t = formatDateTime(v, '')
    if (!t) return null
    const d = new Date(t.replace(' ', 'T') + '+08:00')
    return Number.isNaN(d.getTime()) ? null : d.toISOString().replace(/\.\d{3}Z$/, 'Z')
  }
  r.pinned_until = n(data.pinned_until)
  r.publish_at = n(data.publish_at)
  r.expire_at = n(data.expire_at)
  // 确保 publish_locations 为 JSON
  if (typeof r.publish_locations === 'object' && !Array.isArray(r.publish_locations)) {
    // 已是 dict
  } else if (Array.isArray(r.publish_locations)) {
    const d: Record<string, boolean> = {}
    r.publish_locations.forEach((k: string) => (d[k] = true))
    r.publish_locations = d
  }
  // 移除隐藏字段
  delete r.sender_account_type
  delete r.sender_account_id
  delete r.revoked_at
  r.view_count = 0
  r.extra = {}
  // 确保为数组
  for (const k of [
    'target_account_types',
    'target_account_ids',
    'target_dept_ids',
    'target_role_ids',
  ]) {
    if (!Array.isArray(r[k])) r[k] = []
  }
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
      await msgAnnouncementApi.update({ ...payload, id: state.dataId })
      window.$message.success('更新成功')
    } else {
      await msgAnnouncementApi.create(payload)
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

function toggleLocation(key: string, checked: boolean) {
  state.formModel.publish_locations = { ...state.formModel.publish_locations, [key]: checked }
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
          label-width="120"
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
              <NFormItem label="等级" path="severity">
                <DictSelect v-model="state.formModel.severity" dict-code="NOTIFICATION_SEVERITY" />
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
            <NGi :span="2">
              <NFormItem label="目标范围" path="target_scope">
                <DictSelect
                  v-model="state.formModel.target_scope"
                  dict-code="TARGET_SCOPE"
                  type="radio"
                />
              </NFormItem>
            </NGi>
            <NGi v-if="state.formModel.target_scope !== 'ALL'">
              <NFormItem label="目标账户类型" path="target_account_types">
                <DictSelect
                  v-model="state.formModel.target_account_types"
                  dict-code="ACCOUNT_TYPE"
                  type="checkbox"
                />
              </NFormItem>
            </NGi>

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
            <NGi>
              <NFormItem label="过期时间" path="expire_at">
                <NDatePicker
                  v-model:formatted-value="state.formModel.expire_at"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  class="w-full"
                  clearable
                />
              </NFormItem>
            </NGi>
            <NGi>
              <NFormItem label="是否置顶" path="is_pinned">
                <NSwitch v-model:value="state.formModel.is_pinned" />
              </NFormItem>
            </NGi>
            <NGi v-if="state.formModel.is_pinned">
              <NFormItem label="置顶截止" path="pinned_until">
                <NDatePicker
                  v-model:formatted-value="state.formModel.pinned_until"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  class="w-full"
                  clearable
                />
              </NFormItem>
            </NGi>
          </NGrid>

          <!-- 内容编辑器 -->
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

          <!-- 发布位置：直接绑定字典的独立复选框 -->
          <NFormItem label="发布位置">
            <NFlex>
              <NCheckbox
                v-for="opt in locationOptions"
                :key="opt.value"
                :checked="!!state.formModel.publish_locations?.[opt.value]"
                @update:checked="(v) => toggleLocation(opt.value, v)"
              >
                {{ opt.label }}
              </NCheckbox>
            </NFlex>
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
