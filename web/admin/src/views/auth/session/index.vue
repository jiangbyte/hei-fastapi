<!-- Author: Charlie -->

<script setup lang="tsx">
import type { DataTableColumns, PaginationProps } from 'naive-ui'
import type { ProDataTableColumns, ProSearchFormColumns } from 'pro-naive-ui'
import { Icon } from '@iconify/vue/offline'
import { sessionApi } from '@/api'
import {
  createTagColor,
  formatDateTime,
  hasPermission,
  normalizeSearchValues,
  renderButtonIcon,
} from '@/utils'
import { dictList, dictTypeColor, dictTypeData } from '@/utils/dict'
import { NButton, NDataTable, NFlex, NIcon, NTag } from 'naive-ui'
import { createProSearchForm, ProCard, ProDataTable, ProSearchForm } from 'pro-naive-ui'
import { computed, onMounted, reactive } from 'vue'
import { readPageMeta } from '@/utils/wire'

const state = reactive({
  rows: [] as any[],
  tokens: [] as any[],
  analysis: {} as any,
  total: 0,
  loading: false,
  tokenModalShow: false,
  searchValues: {} as any,
  page: 1,
  pageSize: 20,
})

const searchForm = createProSearchForm<any>({
  defaultCollapsed: true,
  onSubmit(values) {
    state.searchValues = normalizeSearchValues(values, {
      account: (value) => String(value).trim(),
      ip: (value) => String(value).trim(),
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

const analysisCards = computed(() => [
  { key: 'online_account_count', icon: 'icon-park-outline:people', color: '#2563eb' },
  { key: 'online_token_count', icon: 'icon-park-outline:devices', color: '#0f766e' },
  { key: 'admin_account_count', icon: 'icon-park-outline:permissions', color: '#7c3aed' },
  { key: 'portal_account_count', icon: 'icon-park-outline:user', color: '#0891b2' },
  { key: 'one_hour_new_count', icon: 'icon-park-outline:time', color: '#f59e0b' },
  { key: 'max_token_count', icon: 'icon-park-outline:connection', color: '#dc2626' },
])
const analysisTitleMap: Record<string, string> = {
  online_account_count: '在线账号数',
  online_token_count: '在线设备数',
  admin_account_count: '管理端账号数',
  portal_account_count: '门户端账号数',
  one_hour_new_count: '近 1 小时登录数',
  max_token_count: '单账号最大设备数',
}

const searchColumns = computed<ProSearchFormColumns<any>>(() => [
  {
    title: '账号类型',
    path: 'account_type',
    field: 'select',
    fieldProps: { options: dictList('ACCOUNT_TYPE') },
  },
  { title: '账号', path: 'account', field: 'input' },
  { title: '客户端 IP', path: 'ip', field: 'input' },
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
  { title: '账号 ID', path: 'account_id', width: 170, ellipsis: { tooltip: true } },
  {
    title: '账号类型',
    path: 'account_type',
    width: 130,
    render: (row) => (
      <NTag
        color={createTagColor(dictTypeColor('ACCOUNT_TYPE', row.account_type))}
        bordered={false}
      >
        {dictTypeData('ACCOUNT_TYPE', row.account_type) || row.account_type}
      </NTag>
    ),
  },
  { title: '账号', path: 'account', width: 160, ellipsis: { tooltip: true } },
  { title: '名称', path: 'name', width: 160, ellipsis: { tooltip: true } },
  { title: '设备数', path: 'token_count', width: 110 },
  {
    title: '客户端 IP',
    key: 'client_ip',
    width: 150,
    render: (row) => row.tokens?.[0]?.client_ip || row.latest_login_ip || '-',
  },
  {
    title: '设备',
    key: 'device',
    width: 140,
    render: (row) => row.tokens?.[0]?.device_label || '-',
  },
  {
    title: '最近活跃时间',
    path: 'latest_active_at',
    width: 190,
    ellipsis: { tooltip: true },
    render: (row) => formatDateTime(row.latest_active_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 130,
    fixed: 'right',
    render: (row) => (
      <NFlex size={12}>
        {hasPermission('auth:session:tokenlist') ? (
          <NButton type="info" size="small" text={true} onClick={() => openTokens(row)}>
            {renderButtonIcon('icon-park-outline:preview-open')}
          </NButton>
        ) : null}
        {hasPermission('auth:session:exit') ? (
          <NButton type="error" size="small" text={true} onClick={() => confirmExitAccount(row)}>
            {renderButtonIcon('icon-park-outline:logout')}
          </NButton>
        ) : null}
      </NFlex>
    ),
  },
])

const tokenColumns = computed<DataTableColumns<any>>(() => [
  { title: '令牌', key: 'token', width: 220, ellipsis: { tooltip: true } },
  { title: '设备', key: 'device_label', width: 110 },
  { title: '客户端 IP', key: 'client_ip', width: 140 },
  {
    title: '登录时间',
    key: 'login_at',
    width: 180,
    ellipsis: { tooltip: true },
    render: (row) => formatDateTime(row.login_at),
  },
  {
    title: '上次活跃时间',
    key: 'last_active_at',
    width: 180,
    ellipsis: { tooltip: true },
    render: (row) => formatDateTime(row.last_active_at),
  },
  {
    title: '过期时间',
    key: 'expires_at',
    width: 180,
    ellipsis: { tooltip: true },
    render: (row) => formatDateTime(row.expires_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    fixed: 'right',
    render: (row) =>
      hasPermission('auth:session:tokenexit') ? (
        <NButton type="error" size="small" text={true} onClick={() => confirmExitToken(row.token)}>
          {renderButtonIcon('icon-park-outline:logout')}
        </NButton>
      ) : null,
  },
])

onMounted(fetchAll)

async function fetchAll() {
  await Promise.all([fetchAnalysis(), fetchPage()])
}

async function fetchAnalysis() {
  const response = await sessionApi.analysis()
  state.analysis = response.data ?? {}
}

async function fetchPage() {
  state.loading = true
  try {
    const response = await sessionApi.page({
      current: state.page,
      size: state.pageSize,
      ...state.searchValues,
    })
    const data = response.data ?? {}
    state.rows = data.records ?? []
    const pageMeta = readPageMeta(data, { current: state.page, size: state.pageSize })
    state.total = pageMeta.total
    state.page = pageMeta.current
    state.pageSize = pageMeta.size
  } finally {
    state.loading = false
  }
}

function openTokens(row: any) {
  state.tokens = row.tokens ?? []
  state.tokenModalShow = true
}

function confirmExitAccount(row: any) {
  window.$dialog.warning({
    title: '强制下线',
    draggable: true,
    maskClosable: false,
    content: '强制下线该账号的所有在线设备?',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      await sessionApi.exit({
        targets: [{ account_type: row.account_type, account_id: row.account_id }],
      })
      window.$message.success('强制下线成功')
      await fetchAll()
    },
  })
}

function confirmExitToken(token: string) {
  window.$dialog.warning({
    title: '强制下线',
    draggable: true,
    maskClosable: false,
    content: '强制下线该在线设备?',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      await sessionApi.tokenExit({ tokens: [token] })
      window.$message.success('强制下线成功')
      state.tokens = state.tokens.filter((item) => item.token !== token)
      await fetchAll()
    },
  })
}
</script>

<template>
  <NFlex class="h-full min-h-0" vertical>
    <NGrid cols="2 s:3 xl:6" responsive="screen" :x-gap="10" :y-gap="10">
      <NGridItem v-for="item in analysisCards" :key="item.key">
        <NCard class="session-stat" :bordered="false">
          <div
            class="session-stat__icon"
            :style="{ color: item.color, backgroundColor: `${item.color}14` }"
          >
            <NovaIcon :icon="item.icon" :size="22" />
          </div>
          <div class="session-stat__title">
            {{ analysisTitleMap[item.key] ?? item.key }}
          </div>
          <div class="session-stat__value">
            {{ state.analysis[item.key] ?? 0 }}
          </div>
        </NCard>
      </NGridItem>
    </NGrid>

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
      :title="'在线会话'"
      row-key="account_id"
      :scroll-x="1340"
      :columns="tableColumns"
      :data="state.rows"
      :loading="state.loading"
      :pagination="pagination"
    >
      <template #toolbar>
        <NButton
          text
          :title="'刷新'"
          :aria-label="'刷新'"
          :loading="state.loading"
          @click="fetchAll"
        >
          <template #icon>
            <NIcon>
              <Icon icon="icon-park-outline:reload" />
            </NIcon>
          </template>
        </NButton>
      </template>
    </ProDataTable>

    <NModal
      v-model:show="state.tokenModalShow"
      preset="card"
      draggable
      :title="'设备详情'"
      style="width: min(960px, calc(100vw - 32px))"
    >
      <NScrollbar class="h-[540px]">
        <NDataTable
          :row-key="(row) => row.token"
          :scroll-x="1170"
          :columns="tokenColumns"
          :data="state.tokens"
          :pagination="false"
        />
      </NScrollbar>
    </NModal>
  </NFlex>
</template>

<style scoped>
.session-stat :deep(.n-card__content) {
  display: grid;
  gap: 8px;
  min-height: 118px;
}

.session-stat__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
}

.session-stat__title {
  color: var(--text-color-3);
  font-size: 13px;
}

.session-stat__value {
  color: var(--text-color-base);
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
}
</style>
