<!-- Author: Charlie -->

<script setup lang="tsx">
import type { DataTableColumns } from 'naive-ui'
import { accountApi, roleApi } from '@/api'
import { createTagColor, renderButtonIcon } from '@/utils'
import { dictTypeColor, dictTypeData } from '@/utils/dict'
import { NButton, NTag } from 'naive-ui'
import { computed, reactive } from 'vue'

export type RolePickItem = { id: string; name: string; code?: string }

const emit = defineEmits<{
  saved: []
  confirm: [items: RolePickItem[]]
}>()

const state = reactive({
  showModal: false,
  /** grant=账号授权；pick=纯选择（配置/消息等） */
  mode: 'grant' as 'grant' | 'pick',
  multiple: true,
  titleOverride: '',
  loading: false,
  submitLoading: false,
  searchKey: '',
  account: {} as any,
  /** 当前页候选 */
  items: [] as any[],
  selectedData: [] as any[],
  page: 1,
  pageSize: 10,
  total: 0,
})

const isPick = computed(() => state.mode === 'pick')

const modalTitle = computed(() => {
  if (state.titleOverride) return state.titleOverride
  if (isPick.value) return '选择角色'
  return state.account?.name ? `分配角色 - ${state.account.name}` : '分配角色'
})

const selectedIds = computed(() => new Set(state.selectedData.map((item) => String(item.id))))

const listColumns = computed<DataTableColumns<any>>(() => [
  {
    title: '操作',
    key: 'action',
    align: 'center',
    width: 56,
    render: (row) => (
      <NButton
        text
        type="primary"
        size="small"
        disabled={selectedIds.value.has(String(row.id))}
        onClick={() => addRecord(row)}
      >
        {renderButtonIcon('icon-park-outline:plus')}
      </NButton>
    ),
  },
  {
    title: '角色编码',
    key: 'code',
    minWidth: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '名称',
    key: 'name',
    minWidth: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'status',
    width: 110,
    render: (row) => (
      <NTag color={createTagColor(dictTypeColor('COMMON_STATUS', row.status))} bordered={false}>
        {dictTypeData('COMMON_STATUS', row.status) || row.status}
      </NTag>
    ),
  },
])

const selectedColumns = computed<DataTableColumns<any>>(() => [
  {
    title: '操作',
    key: 'action',
    align: 'center',
    width: 70,
    render: (row) => (
      <NButton text type="error" size="small" onClick={() => delRecord(row)}>
        {renderButtonIcon('icon-park-outline:delete')}
      </NButton>
    ),
  },
  {
    title: '名称',
    key: 'name',
    minWidth: 120,
    ellipsis: { tooltip: true },
  },
])

/** 账号授权 */
async function openModal(account: any) {
  state.mode = 'grant'
  state.multiple = true
  state.titleOverride = ''
  state.account = account ?? {}
  state.searchKey = ''
  state.items = []
  state.selectedData = []
  state.page = 1
  state.total = 0
  state.showModal = true
  await Promise.all([fetchGrantedSelected(), fetchCandidatePage()])
}

/** 纯选择：配置默认角色、消息目标等 */
async function openPicker(options?: {
  selectedIds?: string[]
  multiple?: boolean
  title?: string
}) {
  state.mode = 'pick'
  state.multiple = options?.multiple ?? false
  state.titleOverride = options?.title || ''
  state.account = {}
  state.searchKey = ''
  state.items = []
  state.selectedData = []
  state.page = 1
  state.total = 0
  state.showModal = true
  await Promise.all([resolveSelected(options?.selectedIds ?? []), fetchCandidatePage()])
}

/** grant：own-role 仅返回已授权角色 */
async function fetchGrantedSelected() {
  if (!state.account?.id) return
  const response = await accountApi.ownRoles(state.account.id)
  state.selectedData = response.data?.roles ?? []
}

async function fetchCandidatePage() {
  state.loading = true
  try {
    const keyword = state.searchKey.trim()
    const response = await roleApi.page({
      current: state.page,
      size: state.pageSize,
      ...(keyword ? { name: keyword } : {}),
    })
    state.items = response.data?.records ?? []
    state.total = Number(response.data?.total ?? 0)
  } finally {
    state.loading = false
  }
}

/** pick 回显：按 id 逐条 detail */
async function resolveSelected(ids: string[]) {
  const unique = [...new Set(ids.map(String).filter(Boolean))]
  if (!unique.length) {
    state.selectedData = []
    return
  }
  const rows = await Promise.all(
    unique.map(async (id) => {
      try {
        const res = await roleApi.detail({ id })
        const data = res?.data
        return {
          id,
          name: data?.name || data?.code || id,
          code: data?.code,
          status: data?.status,
        }
      } catch {
        return { id, name: id, code: '' }
      }
    }),
  )
  state.selectedData = rows
}

async function submit() {
  if (isPick.value) {
    emit(
      'confirm',
      state.selectedData.map((item) => ({
        id: String(item.id),
        name: item.name || item.code || String(item.id),
        code: item.code,
      })),
    )
    closeModal()
    return
  }

  state.submitLoading = true
  try {
    await accountApi.grantRoles({
      id: state.account.id,
      role_ids: state.selectedData.map((item) => item.id),
    })
    window.$message.success('授权保存成功')
    closeModal()
    emit('saved')
  } finally {
    state.submitLoading = false
  }
}

function closeModal() {
  state.items = []
  state.selectedData = []
  state.total = 0
  state.showModal = false
  state.submitLoading = false
}

function addRecord(record: any) {
  if (isPick.value && !state.multiple) {
    state.selectedData = [record]
    return
  }
  if (!selectedIds.value.has(String(record.id))) {
    state.selectedData.push(record)
  }
}

function addAllPageRecord() {
  if (isPick.value && !state.multiple) return
  state.items.forEach(addRecord)
}

function delRecord(record: any) {
  state.selectedData = state.selectedData.filter((item) => String(item.id) !== String(record.id))
}

function delAllRecord() {
  state.selectedData = []
}

function doSearch() {
  state.page = 1
  void fetchCandidatePage()
}

function resetSearch() {
  state.searchKey = ''
  state.page = 1
  void fetchCandidatePage()
}

function onPageChange(page: number) {
  state.page = page
  void fetchCandidatePage()
}

function onPageSizeChange(size: number) {
  state.pageSize = size
  state.page = 1
  void fetchCandidatePage()
}

defineExpose({ openModal, openPicker })
</script>

<template>
  <NDrawer
    v-model:show="state.showModal"
    :default-width="800"
    placement="right"
    resizable
    :mask-closable="false"
  >
    <NDrawerContent
      :title="modalTitle"
      closable
      :native-scrollbar="false"
    >
      <NGrid
        :cols="24"
        :x-gap="10"
      >
        <NGi :span="16">
          <NSpace vertical>
            <NInputGroup>
              <NInput
                v-model:value="state.searchKey"
                clearable
                placeholder="请输入角色名称"
                @keyup.enter="doSearch"
                @clear="resetSearch"
              />
              <NButton
                type="primary"
                @click="doSearch"
              >
                搜索
              </NButton>
              <NButton @click="resetSearch">
                重置
              </NButton>
            </NInputGroup>
            <NFlex
              justify="space-between"
              align="center"
            >
              <NText>{{ `待处理: ${state.total}` }}</NText>
              <NButton
                v-if="!(isPick && !state.multiple)"
                dashed
                size="small"
                @click="addAllPageRecord"
              >
                新增当前页
              </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(row: any) => row.id"
              :columns="listColumns"
              :data="state.items"
              :loading="state.loading"
              :bordered="true"
              :single-line="false"
              max-height="calc(100vh - 320px)"
            />
            <NPagination
              :page="state.page"
              :page-size="state.pageSize"
              show-size-picker
              size="small"
              :item-count="state.total"
              :page-sizes="[10, 20, 50, 100]"
              @update:page="onPageChange"
              @update:page-size="onPageSizeChange"
            />
          </NSpace>
        </NGi>
        <NGi :span="8">
          <NSpace vertical>
            <NFlex
              justify="space-between"
              align="center"
            >
              <NText>{{ `已选择: ${state.selectedData.length}` }}</NText>
              <NButton
                dashed
                type="error"
                size="small"
                @click="delAllRecord"
              >
                全部移除
              </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(row: any) => row.id"
              :columns="selectedColumns"
              :data="state.selectedData"
              :bordered="true"
              :single-line="false"
              max-height="calc(100vh - 260px)"
            />
          </NSpace>
        </NGi>
      </NGrid>
      <template #footer>
        <NSpace
          justify="end"
          align="center"
        >
          <NButton @click="closeModal">
            关闭
          </NButton>
          <NButton
            type="primary"
            :loading="state.submitLoading"
            @click="submit"
          >
            {{ isPick ? '确认' : '保存' }}
          </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
