<!-- Author: Charlie -->

<script setup lang="tsx">
import type { DataTableColumns } from 'naive-ui'
import { accountApi, deptApi } from '@/api'
import { renderButtonIcon } from '@/utils'
import { NButton, NTag } from 'naive-ui'
import { computed, reactive } from 'vue'

const emit = defineEmits<{ saved: [] }>()

interface FlatDept {
  id: string
  name: string
  depth: number
}

const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  searchKey: '',
  account: {} as any,
  flatDepts: [] as FlatDept[],
  selectedData: [] as FlatDept[],
  primaryId: null as string | null,
  page: 1,
  pageSize: 20,
})

const modalTitle = computed(() =>
  state.account?.name ? `分配部门 - ${state.account.name}` : '分配部门',
)

const filteredDepts = computed(() => {
  const k = state.searchKey.trim().toLowerCase()
  return k ? state.flatDepts.filter((d) => d.name.toLowerCase().includes(k)) : state.flatDepts
})

const tableDepts = computed(() => {
  const s = (state.page - 1) * state.pageSize
  return filteredDepts.value.slice(s, s + state.pageSize)
})

const selectedIds = computed(() => new Set(state.selectedData.map((d) => d.id)))

const listColumns = computed<DataTableColumns<FlatDept>>(() => [
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
        disabled={selectedIds.value.has(row.id)}
        onClick={() => addRecord(row)}
      >
        {renderButtonIcon('icon-park-outline:plus')}
      </NButton>
    ),
  },
  {
    title: '部门名称',
    key: 'name',
    minWidth: 160,
    render: (row) => <span style={{ paddingLeft: `${row.depth * 16}px` }}>{row.name}</span>,
  },
])

const selectedColumns = computed<DataTableColumns<FlatDept>>(() => [
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
  { title: '部门名称', key: 'name', minWidth: 120 },
  {
    title: '主部门',
    key: 'primary',
    width: 90,
    render: (row) =>
      state.primaryId === row.id ? (
        <NTag type="success" size="small" bordered={false}>
          主部门
        </NTag>
      ) : (
        <NButton text size="small" type="primary" onClick={() => (state.primaryId = row.id)}>
          设为主部门
        </NButton>
      ),
  },
])

async function openModal(account: any) {
  state.account = account ?? {}
  state.searchKey = ''
  state.flatDepts = []
  state.selectedData = []
  state.primaryId = null
  state.page = 1
  state.showModal = true
  await fetchData()
}

async function fetchData() {
  if (!state.account?.id) return
  state.loading = true
  try {
    const [deptRes, grantRes] = await Promise.all([
      deptApi.tree().catch(() => ({ data: [] })),
      accountApi.ownDepts(state.account.id),
    ])
    state.flatDepts = flattenTree(deptRes.data ?? [])
    const infoList = grantRes.data?.grant_info_list ?? []
    const selIds = new Set(infoList.map((i: any) => String(i.dept_id)))
    state.selectedData = state.flatDepts.filter((d) => selIds.has(d.id))
    const primary = infoList.find((i: any) => i.is_primary)?.dept_id
    state.primaryId = primary ? String(primary) : (state.selectedData[0]?.id ?? null)
  } finally {
    state.loading = false
  }
}

async function submitGrant() {
  state.submitLoading = true
  try {
    const ids = state.selectedData.map((d) => d.id)
    const primary = state.primaryId && ids.includes(state.primaryId) ? state.primaryId : ids[0]
    await accountApi.grantDepts({
      id: state.account.id,
      grant_info_list: ids.map((id) => ({ dept_id: id, is_primary: id === primary })),
    })
    window.$message.success('授权保存成功')
    closeModal()
    emit('saved')
  } finally {
    state.submitLoading = false
  }
}

function flattenTree(nodes: any[], depth = 0): FlatDept[] {
  const result: FlatDept[] = []
  for (const n of nodes) {
    result.push({ id: String(n.id), name: n.name, depth })
    if (n.children) result.push(...flattenTree(n.children, depth + 1))
  }
  return result
}

function closeModal() {
  state.flatDepts = []
  state.selectedData = []
  state.primaryId = null
  state.showModal = false
  state.submitLoading = false
}
function addRecord(r: FlatDept) {
  if (!selectedIds.value.has(r.id)) state.selectedData.push(r)
}
function addAllPageRecord() {
  tableDepts.value.forEach(addRecord)
}
function delRecord(r: FlatDept) {
  state.selectedData = state.selectedData.filter((d) => d.id !== r.id)
  if (state.primaryId === r.id) state.primaryId = state.selectedData[0]?.id ?? null
}
function delAllRecord() {
  state.selectedData = []
  state.primaryId = null
}
function resetSearch() {
  state.searchKey = ''
  state.page = 1
}
defineExpose({ openModal })
</script>

<template>
  <NDrawer
    v-model:show="state.showModal"
    :default-width="900"
    placement="right"
    resizable
    :mask-closable="false"
  >
    <NDrawerContent :title="modalTitle" closable :native-scrollbar="false">
      <NGrid :cols="24" :x-gap="10">
        <NGi :span="15">
          <NSpace vertical>
            <NInputGroup>
              <NInput
                v-model:value="state.searchKey"
                clearable
                placeholder="搜索部门"
                @keyup.enter="state.page = 1"
                @clear="resetSearch"
              />
              <NButton type="primary" @click="state.page = 1"> 搜索 </NButton>
              <NButton @click="resetSearch"> 重置 </NButton>
            </NInputGroup>
            <NFlex justify="space-between" align="center">
              <NText>{{ `待处理: ${filteredDepts.length}` }}</NText>
              <NButton dashed size="small" @click="addAllPageRecord"> 新增当前页 </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(r: FlatDept) => r.id"
              :columns="listColumns"
              :data="tableDepts"
              :loading="state.loading"
              :bordered="true"
              :single-line="false"
              max-height="calc(100vh - 320px)"
            />
            <NPagination
              v-model:page="state.page"
              v-model:page-size="state.pageSize"
              show-size-picker
              size="small"
              :item-count="filteredDepts.length"
              :page-sizes="[10, 20, 50, 100]"
            />
          </NSpace>
        </NGi>
        <NGi :span="9">
          <NSpace vertical>
            <NFlex justify="space-between" align="center">
              <NText>{{ `已选择: ${state.selectedData.length}` }}</NText>
              <NButton dashed type="error" size="small" @click="delAllRecord"> 全部移除 </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(r: FlatDept) => r.id"
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
        <NSpace justify="end" align="center">
          <NButton @click="closeModal"> 关闭 </NButton>
          <NButton type="primary" :loading="state.submitLoading" @click="submitGrant">
            保存
          </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
