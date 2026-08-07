<!-- Author: Charlie -->

<script setup lang="tsx">
import type { PaginationProps } from 'naive-ui'
import type { ProDataTableColumns, ProSearchFormColumns } from 'pro-naive-ui'
import { Icon } from '@iconify/vue/offline'
import { accountApi } from '@/api'
import {
  createTagColor,
  formatDateTime,
  hasPermission,
  normalizeSearchValues,
  renderButtonIcon,
  resolveFileUrl,
} from '@/utils'
import { NAvatar, NButton, NDropdown, NFlex, NIcon, NTag } from 'naive-ui'
import { createProSearchForm, ProCard, ProDataTable, ProSearchForm } from 'pro-naive-ui'
import { computed, onMounted, reactive, ref } from 'vue'
import { dictList, dictTypeData, dictTypeColor } from '@/utils/dict'
import ModalDetail from './components/ModalDetail.vue'
import ModalForm from './components/ModalForm.vue'
import ModalGrantDept from '../components/ModalGrantDept.vue'
import ModalGrantResource from '../role/components/ModalGrantResource.vue'
import ModalGrantGroup from '../components/ModalGrantGroup.vue'
import ModalGrantRole from '../components/ModalGrantRole.vue'
import { readPageMeta } from '@/utils/wire'

const formModalRef = ref<any>(null)
const detailModalRef = ref<any>(null)
const grantRoleModalRef = ref<any>(null)
const grantGroupModalRef = ref<any>(null)
const grantDeptModalRef = ref<any>(null)
const grantResourceModalRef = ref<any>(null)
const state = reactive({
  accounts: [] as any[],
  total: 0,
  loading: false,
  searchValues: {} as any,
  checkedRowKeys: [] as string[],
  page: 1,
  pageSize: 20,
})

const searchForm = createProSearchForm<any>({
  defaultCollapsed: true,
  onSubmit(values) {
    state.searchValues = normalizeSearchValues(values, {
      account: (value) => String(value).trim(),
      name: (value) => String(value).trim(),
      phone: (value) => String(value).trim(),
      email: (value) => String(value).trim(),
    })
    state.page = 1
    fetchPage()
  },
  onReset() {
    state.searchValues = {}
    state.page = 1
    fetchPage()
  },
})

const searchColumns = computed<ProSearchFormColumns<any>>(() => [
  {
    title: '账号',
    path: 'account',
    field: 'input',
  },
  {
    title: '名称',
    path: 'name',
    field: 'input',
  },
  {
    title: '手机号',
    path: 'phone',
    field: 'input',
  },
  {
    title: '邮箱',
    path: 'email',
    field: 'input',
  },
  {
    title: '账号类型',
    path: 'account_type',
    field: 'select',
    fieldProps: {
      options: dictList('ACCOUNT_TYPE'),
    },
  },
  {
    title: '账号状态',
    path: 'account_status',
    field: 'select',
    fieldProps: {
      options: dictList('ACCOUNT_STATUS'),
    },
  },
])

const pagination = computed<PaginationProps>(() => ({
  page: state.page,
  pageSize: state.pageSize,
  itemCount: state.total,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `${itemCount} 条`,
  onUpdatePage: (value) => {
    state.page = value
    fetchPage()
  },
  onUpdatePageSize: (value) => {
    state.pageSize = value
    state.page = 1
    fetchPage()
  },
}))

const tableColumns = computed<ProDataTableColumns<any>>(() => [
  {
    type: 'selection',
    fixed: 'left',
  },
  {
    title: '头像',
    key: 'avatar',
    width: 80,
    render: (row) => renderAvatar(row),
  },
  {
    title: '账号',
    path: 'account',
    width: 140,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '名称',
    path: 'name',
    width: 130,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '昵称',
    path: 'nickname',
    width: 130,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '账号类型',
    path: 'account_type',
    width: 120,
    render: (row) => (
      <NTag
        color={createTagColor(dictTypeColor('ACCOUNT_TYPE', row.account_type))}
        bordered={false}
      >
        {dictTypeData('ACCOUNT_TYPE', row.account_type)}
      </NTag>
    ),
  },
  {
    title: '账号状态',
    path: 'account_status',
    width: 120,
    render: (row) => (
      <NTag
        color={createTagColor(dictTypeColor('ACCOUNT_STATUS', row.account_status))}
        bordered={false}
      >
        {dictTypeData('ACCOUNT_STATUS', row.account_status)}
      </NTag>
    ),
  },
  {
    title: '手机号',
    path: 'phone',
    width: 150,
  },
  {
    title: '邮箱',
    path: 'email',
    width: 220,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '最近登录时间',
    path: 'latest_login_time',
    width: 190,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => formatDateTime(row.latest_login_time),
  },
  {
    title: '更新时间',
    path: 'updated_at',
    width: 190,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => formatDateTime(row.updated_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    render: (row) => {
      const options = grantOptions.value
      return (
        <NFlex size={12}>
          {hasPermission('iam:account:detail') ? (
            <NButton type="info" size="small" text={true} onClick={() => openDetailModal(row.id)}>
              {renderButtonIcon('icon-park-outline:preview-open')}
            </NButton>
          ) : null}
          {hasPermission('iam:account:update') ? (
            <NButton type="primary" size="small" text={true} onClick={() => openEditModal(row.id)}>
              {renderButtonIcon('icon-park-outline:edit')}
            </NButton>
          ) : null}
          {options.length ? (
            <NDropdown
              trigger="click"
              options={options}
              onSelect={(key) => openGrantModal(String(key), row)}
            >
              <NButton type="warning" size="small" text={true}>
                {renderButtonIcon('icon-park-outline:permissions')}
              </NButton>
            </NDropdown>
          ) : null}
          {hasPermission('iam:account:delete') ? (
            <NButton type="error" size="small" text={true} onClick={() => confirmDelete(row.id)}>
              {renderButtonIcon('icon-park-outline:delete')}
            </NButton>
          ) : null}
        </NFlex>
      )
    },
  },
])

const grantOptions = computed(() =>
  [
    {
      label: '分配角色',
      key: 'role',
      permission: 'iam:account:grantrole',
    },
    {
      label: '分配用户组',
      key: 'group',
      permission: 'iam:account:grantgroup',
    },
    {
      label: '分配部门',
      key: 'dept',
      permission: 'iam:account:grantdept',
    },
    {
      label: '分配资源',
      key: 'resource',
      permission: 'iam:account:grantresource',
    },
  ].filter((item) => hasPermission(item.permission)),
)
const hasCheckedRows = computed(() => state.checkedRowKeys.length > 0)
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

onMounted(() => {
  fetchPage()
})

async function fetchPage() {
  state.loading = true
  try {
    const response = await accountApi.page({
      current: state.page,
      size: state.pageSize,
      ...state.searchValues,
    })
    const data = response.data ?? {}
    state.accounts = data.records ?? []
    const pageMeta = readPageMeta(data, { current: state.page, size: state.pageSize })
    state.total = pageMeta.total
    state.page = pageMeta.current
    state.pageSize = pageMeta.size
    state.checkedRowKeys = state.checkedRowKeys.filter((key) =>
      state.accounts.some((item) => item.id === key),
    )
  } finally {
    state.loading = false
  }
}

function openDetailModal(id: string) {
  detailModalRef.value?.openModal(id)
}

function renderAvatar(row: any) {
  const avatar = resolveFileUrl(row.avatar)
  const name = row.nickname || row.name || row.account || ''
  return (
    <NAvatar round size={32} src={avatar} imgProps={avatarImgProps}>
      {avatar
        ? undefined
        : String(name || '-')
            .slice(0, 1)
            .toUpperCase()}
    </NAvatar>
  )
}

function openCreateModal() {
  formModalRef.value?.openModal()
}

function openEditModal(id: string) {
  formModalRef.value?.openModal(id)
}

function openGrantModal(type: string, row: any) {
  const account = {
    id: row.id,
    code: row.account,
    name: row.nickname || '-',
  }
  if (type === 'role') {
    grantRoleModalRef.value?.openModal(account)
  } else if (type === 'group') {
    grantGroupModalRef.value?.openModal(account)
  } else if (type === 'dept') {
    grantDeptModalRef.value?.openModal(account)
  } else if (type === 'resource') {
    grantResourceModalRef.value?.openModal(account, accountApi, '分配资源')
  }
}

function handleCheckedRowKeys(keys: Array<string | number>) {
  state.checkedRowKeys = keys.map(String)
}

function confirmDelete(value: string | string[]) {
  const ids = Array.isArray(value) ? value : [value]
  if (!ids.length) {
    return
  }
  const isBatch = ids.length > 1

  window.$dialog.warning({
    title: isBatch ? '批量删除' : '删除',
    draggable: true,
    maskClosable: false,
    content: isBatch ? `删除 ${ids.length} 个账号?` : '删除该账号?',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: () => deleteData(ids),
  })
}

async function deleteData(ids: string[]) {
  await accountApi.remove({ ids })
  state.checkedRowKeys = state.checkedRowKeys.filter((key) => !ids.includes(key))

  window.$message.success('删除成功')
  await fetchPage()
  if (!state.accounts.length && state.total > 0 && state.page > 1) {
    state.page -= 1
    await fetchPage()
  }
}
</script>

<template>
  <NFlex class="h-full min-h-0" vertical>
    <ProCard content-class="pb-0!">
      <ProSearchForm
        :form="searchForm"
        :columns="searchColumns"
        :reset-button-props="{ content: '重置' }"
        :search-button-props="{ content: '搜索' }"
        :collapse-button-props="{
          content: searchForm.collapsed.value ? '展开' : '收起',
        }"
      />
    </ProCard>

    <ProDataTable
      class="min-h-0 flex-1"
      remote
      :title="'账号管理'"
      row-key="id"
      :scroll-x="1960"
      :columns="tableColumns"
      :data="state.accounts"
      :loading="state.loading"
      :pagination="pagination"
      :checked-row-keys="state.checkedRowKeys"
      :on-update-checked-row-keys="handleCheckedRowKeys"
    >
      <template #toolbar>
        <NFlex>
          <NButton
            v-if="hasPermission('iam:account:create')"
            type="primary"
            text
            :title="'新增'"
            :aria-label="'新增'"
            @click="openCreateModal"
          >
            <template #icon>
              <NIcon>
                <Icon icon="icon-park-outline:plus" />
              </NIcon>
            </template>
          </NButton>
          <NButton
            text
            :title="'刷新'"
            :aria-label="'刷新'"
            :loading="state.loading"
            @click="fetchPage"
          >
            <template #icon>
              <NIcon>
                <Icon icon="icon-park-outline:reload" />
              </NIcon>
            </template>
          </NButton>
          <NButton
            v-if="hasPermission('iam:account:delete')"
            type="error"
            text
            :title="'批量删除'"
            :aria-label="'批量删除'"
            :disabled="!hasCheckedRows"
            @click="confirmDelete(state.checkedRowKeys)"
          >
            <template #icon>
              <NIcon>
                <Icon icon="icon-park-outline:delete" />
              </NIcon>
            </template>
          </NButton>
        </NFlex>
      </template>
    </ProDataTable>

    <ModalForm ref="formModalRef" @saved="fetchPage" />
    <ModalDetail ref="detailModalRef" />
    <ModalGrantRole ref="grantRoleModalRef" @saved="fetchPage" />
    <ModalGrantGroup ref="grantGroupModalRef" @saved="fetchPage" />
    <ModalGrantDept ref="grantDeptModalRef" @saved="fetchPage" />
    <ModalGrantResource ref="grantResourceModalRef" @saved="fetchPage" />
  </NFlex>
</template>

<style scoped></style>
