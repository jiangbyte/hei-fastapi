<!-- Author: Charlie -->

<script setup lang="tsx">
import type { DataTableColumns } from 'naive-ui'
import { roleApi } from '@/api'
import { NButton } from 'naive-ui'
import { computed, reactive, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    visible: boolean
    mode?: 'single' | 'multiple'
    title?: string
    selected?: string[]
  }>(),
  { mode: 'single', title: '选择角色', selected: () => [] },
)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  select: [value: { id: string; name: string }]
  'update:selected': [value: string[]]
  confirm: [value: string[]]
}>()

const state = reactive({
  loading: false,
  searchKey: '',
  roles: [] as any[],
  total: 0,
  checkedRowKeys: [] as string[],
  page: 1,
  pageSize: 10,
})

const columns = computed<DataTableColumns<any>>(() => {
  const base: DataTableColumns<any> = [
    { title: '名称', key: 'name', minWidth: 120, ellipsis: { tooltip: true } },
    { title: '编码', key: 'code', minWidth: 120, ellipsis: { tooltip: true } },
  ]
  if (props.mode === 'single') {
    base.push({
      title: '操作',
      key: 'action',
      width: 60,
      align: 'center',
      render: (row) => (
        <NButton text type="primary" size="small" onClick={() => doSelect(row)}>
          选择
        </NButton>
      ),
    })
  }
  return base
})

watch(
  () => props.visible,
  (val) => {
    if (val) {
      state.checkedRowKeys = [...props.selected]
      state.searchKey = ''
      state.page = 1
      loadRoles()
    } else {
      state.checkedRowKeys = []
    }
  },
)

async function loadRoles() {
  state.loading = true
  try {
    const params: any = { current: state.page, size: state.pageSize }
    if (state.searchKey.trim()) {
      params.name = state.searchKey.trim()
    }
    const res = await roleApi.page(params)
    state.roles = res?.data?.records ?? []
    state.total = res?.data?.total ?? 0
  } catch {
    state.roles = []
    state.total = 0
  } finally {
    state.loading = false
  }
}

function doSelect(role: any) {
  const result = { id: role.id, name: role.name || role.code || role.id }
  emit('select', result)
  close()
}

function doSearch() {
  state.page = 1
  loadRoles()
}

function handleConfirm() {
  emit('update:selected', [...state.checkedRowKeys])
  emit('confirm', [...state.checkedRowKeys])
  close()
}

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <NDrawer
    :show="visible"
    placement="right"
    :width="500"
    :mask-closable="false"
    @update:show="(v: boolean) => emit('update:visible', v)"
  >
    <NDrawerContent :title="title" closable>
      <NSpace vertical>
        <NInput
          v-model:value="state.searchKey"
          clearable
          placeholder="搜索角色名称"
          @keyup.enter="doSearch"
          @clear="doSearch"
        />
        <NDataTable
          :row-key="(row: any) => row.id"
          :columns="columns"
          :data="state.roles"
          :loading="state.loading"
          :bordered="true"
          :single-line="false"
          max-height="calc(100vh - 260px)"
        />
        <NPagination
          v-model:page="state.page"
          v-model:page-size="state.pageSize"
          show-size-picker
          :item-count="state.total"
          :page-sizes="[10, 20, 50]"
        />
      </NSpace>
      <template v-if="mode === 'multiple'" #footer>
        <NSpace justify="end">
          <NButton @click="close"> 关闭 </NButton>
          <NButton type="primary" @click="handleConfirm"> 确认 </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
