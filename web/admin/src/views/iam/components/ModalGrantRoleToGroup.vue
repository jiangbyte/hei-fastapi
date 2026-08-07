<!-- Author: Charlie -->

<script setup lang="tsx">
import type { DataTableColumns } from 'naive-ui'
import { groupApi } from '@/api'
import { renderButtonIcon } from '@/utils'
import { createTagColor } from '@/utils'
import { dictTypeColor, dictTypeData } from '@/utils/dict'
import { NButton, NTag } from 'naive-ui'
import { computed, reactive } from 'vue'

const emit = defineEmits<{ saved: [] }>()

const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  searchKey: '',
  group: {} as any,
  items: [] as any[],
  selectedData: [] as any[],
  page: 1,
  pageSize: 10,
})

const modalTitle = computed(() =>
  state.group?.name ? `分配角色 - ${state.group.name}` : '分配角色',
)

const filteredItems = computed(() => {
  const keyword = state.searchKey.trim().toLowerCase()
  if (!keyword) return state.items
  return state.items.filter((item) =>
    ['code', 'name'].some((f) =>
      String(item[f] || '')
        .toLowerCase()
        .includes(keyword),
    ),
  )
})

const tableItems = computed(() => {
  const start = (state.page - 1) * state.pageSize
  return filteredItems.value.slice(start, start + state.pageSize)
})

const selectedIds = computed(() => new Set(state.selectedData.map((i) => String(i.id))))

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
  { title: '角色编码', key: 'code', minWidth: 120, ellipsis: { tooltip: true } },
  { title: '名称', key: 'name', minWidth: 120, ellipsis: { tooltip: true } },
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
  { title: '名称', key: 'name', minWidth: 120, ellipsis: { tooltip: true } },
])

async function openModal(group: any) {
  state.group = group ?? {}
  state.searchKey = ''
  state.items = []
  state.selectedData = []
  state.page = 1
  state.showModal = true
  await fetchData()
}

async function fetchData() {
  if (!state.group?.id) return
  state.loading = true
  try {
    const resp = await groupApi.ownRoles(state.group.id)
    state.items = resp.data?.roles ?? []
    const ids = new Set((resp.data?.role_ids ?? []).map(String))
    state.selectedData = state.items.filter((i) => ids.has(String(i.id)))
  } finally {
    state.loading = false
  }
}

async function submitGrant() {
  state.submitLoading = true
  try {
    await groupApi.grantRoles({ id: state.group.id, role_ids: state.selectedData.map((i) => i.id) })
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
  state.showModal = false
  state.submitLoading = false
}
function addRecord(r: any) {
  if (!selectedIds.value.has(String(r.id))) state.selectedData.push(r)
}
function addAllPageRecord() {
  tableItems.value.forEach(addRecord)
}
function delRecord(r: any) {
  state.selectedData = state.selectedData.filter((i) => String(i.id) !== String(r.id))
}
function delAllRecord() {
  state.selectedData = []
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
    :default-width="800"
    placement="right"
    resizable
    :mask-closable="false"
  >
    <NDrawerContent :title="modalTitle" closable :native-scrollbar="false">
      <NGrid :cols="24" :x-gap="10">
        <NGi :span="16">
          <NSpace vertical>
            <NInputGroup>
              <NInput
                v-model:value="state.searchKey"
                clearable
                placeholder="请输入角色编码或名称"
                @keyup.enter="state.page = 1"
                @clear="resetSearch"
              />
              <NButton type="primary" @click="state.page = 1"> 搜索 </NButton>
              <NButton @click="resetSearch"> 重置 </NButton>
            </NInputGroup>
            <NFlex justify="space-between" align="center">
              <NText>{{ `待处理: ${filteredItems.length}` }}</NText>
              <NButton dashed size="small" @click="addAllPageRecord"> 新增当前页 </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(r) => r.id"
              :columns="listColumns"
              :data="tableItems"
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
              :item-count="filteredItems.length"
              :page-sizes="[10, 20, 50, 100]"
            />
          </NSpace>
        </NGi>
        <NGi :span="8">
          <NSpace vertical>
            <NFlex justify="space-between" align="center">
              <NText>{{ `已选择: ${state.selectedData.length}` }}</NText>
              <NButton dashed type="error" size="small" @click="delAllRecord"> 全部移除 </NButton>
            </NFlex>
            <NDataTable
              size="small"
              :row-key="(r) => r.id"
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
