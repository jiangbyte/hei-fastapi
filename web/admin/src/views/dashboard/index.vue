<!-- Author: Charlie -->

<script setup lang="ts">
import { Chart } from '@antv/g2'
import { dashboardApi } from '@/api'
import { useAuthStore } from '@/stores'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NIcon } from 'naive-ui'
import { Icon } from '@iconify/vue/offline'

type ChartInstance = InstanceType<typeof Chart>

const authStore = useAuthStore()
const router = useRouter()
const accountTrendRef = ref<HTMLDivElement | null>(null)
const auditTrendRef = ref<HTMLDivElement | null>(null)
const fileChartRef = ref<HTMLDivElement | null>(null)
const charts: ChartInstance[] = []
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

const state = reactive({
  loading: false,
  chartLoadError: false,
  overview: {
    summary: {
      account_total: 0,
      online_sessions: 0,
      file_total: 0,
      storage_bytes: 0,
    },
    accounts: {
      enabled: 0,
      disabled: 0,
      today_new: 0,
      by_type: [] as Array<{ name: string; value: number }>,
    },
    iam: {
      role_count: 0,
      dept_count: 0,
      group_count: 0,
      menu_count: 0,
    },
    ops_today: {
      audit_total: 0,
      audit_failed: 0,
      feedback_pending: 0,
    },
    trends: {
      account_trend: [] as any[],
      audit_trend: [] as any[],
    },
    files: {
      by_content_type: [] as Array<{ name: string; value: number }>,
    },
  },
})

const bannerMetrics = computed(() => [
  {
    key: 'account_total',
    label: '账号总数',
    value: Number(state.overview.summary.account_total ?? 0),
    hint: `今日新增 ${Number(state.overview.accounts.today_new ?? 0)}`,
  },
  {
    key: 'online_sessions',
    label: '在线设备',
    value: Number(state.overview.summary.online_sessions ?? 0),
    hint: '当前会话',
  },
  {
    key: 'file_total',
    label: '文件数量',
    value: Number(state.overview.summary.file_total ?? 0),
    hint: '个文件',
  },
  {
    key: 'storage_bytes',
    label: '存储用量',
    value: formatFileSize(state.overview.summary.storage_bytes),
    hint: '累计占用',
  },
])

const accountStats = computed(() => [
  { key: 'enabled', label: '启用账号', value: Number(state.overview.accounts.enabled ?? 0) },
  { key: 'disabled', label: '禁用账号', value: Number(state.overview.accounts.disabled ?? 0) },
  { key: 'today_new', label: '今日新增', value: Number(state.overview.accounts.today_new ?? 0) },
  ...state.overview.accounts.by_type.map((item) => ({
    key: `type_${item.name}`,
    label: `类型 ${item.name}`,
    value: Number(item.value ?? 0),
  })),
])

const iamStats = computed(() => [
  { key: 'role', label: '角色', value: Number(state.overview.iam.role_count ?? 0) },
  { key: 'dept', label: '部门', value: Number(state.overview.iam.dept_count ?? 0) },
  { key: 'group', label: '用户组', value: Number(state.overview.iam.group_count ?? 0) },
  { key: 'menu', label: '菜单', value: Number(state.overview.iam.menu_count ?? 0) },
])

const opsTodayStats = computed(() => [
  {
    key: 'audit_total',
    label: '今日审计',
    value: Number(state.overview.ops_today.audit_total ?? 0),
  },
  {
    key: 'audit_failed',
    label: '今日失败',
    value: Number(state.overview.ops_today.audit_failed ?? 0),
  },
  {
    key: 'feedback_pending',
    label: '待处理反馈',
    value: Number(state.overview.ops_today.feedback_pending ?? 0),
  },
])

const accountTrendData = computed(() =>
  state.overview.trends.account_trend.map((item) => ({
    ...item,
    type: '新增账号',
  })),
)

const auditTrendData = computed(() =>
  state.overview.trends.audit_trend.map((item) => ({
    ...item,
    type: '审计量',
  })),
)

const displayName = computed(() => {
  const user = authStore.userInfo
  const nickname = String(user?.nickname ?? '').trim()
  const name = String(user?.name ?? '').trim()
  if (nickname && name && nickname !== name) {
    return `${nickname}（${name}）`
  }
  return nickname || name || user?.account || '-'
})

const avatarUrl = computed(() => authStore.userInfo?.avatar || undefined)
const roleText = computed(() => mapNames(authStore.userInfo?.roleIdNames))
const deptText = computed(() => mapNames(authStore.userInfo?.deptIdNames))
const groupText = computed(() => mapNames(authStore.userInfo?.groupIdNames))

onMounted(fetchOverview)

onBeforeUnmount(() => {
  destroyCharts()
})

watch(
  () => [accountTrendData.value, auditTrendData.value, state.overview.files.by_content_type],
  async () => {
    await nextTick()
    await renderCharts()
  },
)

async function fetchOverview() {
  state.loading = true
  try {
    const response = await dashboardApi.overview()
    state.overview = Object.assign(state.overview, response.data ?? {})
    await nextTick()
    await renderCharts()
  } finally {
    state.loading = false
  }
}

function mapNames(items?: Array<{ id?: string; name?: string }>) {
  return (items ?? [])
    .map((item) => item.name)
    .filter(Boolean)
    .join(' / ')
}

function displayValue(value: unknown) {
  const text = String(value ?? '').trim()
  return text || '未设置'
}

function formatFileSize(size?: number | string | null) {
  const value = Number(size ?? 0)
  if (!Number.isFinite(value) || value <= 0) {
    return '0 B'
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let current = value
  let unitIndex = 0
  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024
    unitIndex += 1
  }
  return `${current.toFixed(unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`
}

async function renderCharts() {
  destroyCharts()
  state.chartLoadError = false
  try {
    await Promise.all([renderAccountTrend(), renderAuditTrend(), renderFileChart()])
  } catch {
    state.chartLoadError = true
  }
}

function destroyCharts() {
  while (charts.length) {
    charts.pop()?.destroy()
  }
}

async function renderLineChart(container: HTMLDivElement | null, data: any[], color: string) {
  if (!container) {
    return
  }
  const chart = new Chart({ container, autoFit: true, height: 260 })
  chart.options({
    type: 'line',
    data,
    encode: { x: 'date', y: 'value', color: 'type' },
    scale: { color: { range: [color] } },
    style: { lineWidth: 2.4 },
    axis: { x: { title: false }, y: { title: false, grid: true } },
    legend: { color: { position: 'top' } },
  })
  charts.push(chart)
  await chart.render()
}

async function renderAccountTrend() {
  await renderLineChart(accountTrendRef.value, accountTrendData.value, '#2563eb')
}

async function renderAuditTrend() {
  await renderLineChart(auditTrendRef.value, auditTrendData.value, '#0f766e')
}

async function renderFileChart() {
  if (!fileChartRef.value) {
    return
  }
  const chart = new Chart({ container: fileChartRef.value, autoFit: true, height: 220 })
  chart.options({
    type: 'interval',
    coordinate: { type: 'theta' },
    data: state.overview.files.by_content_type,
    encode: { y: 'value', color: 'name' },
    transform: [{ type: 'stackY' }],
    legend: { color: { position: 'bottom' } },
    labels: [{ text: 'name', position: 'outside', style: { fontSize: 12 } }],
  })
  charts.push(chart)
  await chart.render()
}

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <NSpin :show="state.loading">
    <n-el class="dashboard-page">
      <NGrid
        cols="1 m:24"
        responsive="screen"
        :x-gap="16"
        :y-gap="16"
      >
        <NGridItem span="1 m:16">
          <NSpace
            vertical
            :size="16"
            style="width: 100%"
          >
            <NCard
              class="dashboard-banner"
              :bordered="false"
              size="small"
            >
              <NGrid
                cols="2 s:4"
                responsive="screen"
                :x-gap="12"
                :y-gap="12"
              >
                <NGridItem
                  v-for="item in bannerMetrics"
                  :key="item.key"
                >
                  <div class="dashboard-banner__item">
                    <div class="dashboard-banner__label">
                      {{ item.label }}
                    </div>
                    <div class="dashboard-banner__value">
                      {{ item.value }}
                    </div>
                    <div class="dashboard-banner__hint">
                      {{ item.hint }}
                    </div>
                  </div>
                </NGridItem>
              </NGrid>
            </NCard>

            <NCard
              title="账号健康度"
              :bordered="false"
              size="small"
            >
              <template #header-extra>
                <NButton
                  text
                  :loading="state.loading"
                  @click="fetchOverview"
                >
                  <template #icon>
                    <NIcon>
                      <Icon icon="icon-park-outline:reload" />
                    </NIcon>
                  </template>
                  刷新
                </NButton>
              </template>
              <NGrid
                cols="2 s:4"
                responsive="screen"
                :x-gap="16"
                :y-gap="16"
              >
                <NGridItem
                  v-for="item in accountStats"
                  :key="item.key"
                >
                  <NStatistic
                    :label="item.label"
                    :value="item.value"
                  />
                </NGridItem>
              </NGrid>
            </NCard>

            <NCard
              title="组织与菜单"
              :bordered="false"
              size="small"
            >
              <NGrid
                cols="2 s:4"
                responsive="screen"
                :x-gap="16"
                :y-gap="16"
              >
                <NGridItem
                  v-for="item in iamStats"
                  :key="item.key"
                >
                  <NStatistic
                    :label="item.label"
                    :value="item.value"
                  />
                </NGridItem>
              </NGrid>
            </NCard>

            <NCard
              title="今日运维"
              :bordered="false"
              size="small"
            >
              <NGrid
                cols="1 s:3"
                responsive="screen"
                :x-gap="16"
                :y-gap="16"
              >
                <NGridItem
                  v-for="item in opsTodayStats"
                  :key="item.key"
                >
                  <NStatistic
                    :label="item.label"
                    :value="item.value"
                  />
                </NGridItem>
              </NGrid>
            </NCard>

            <NCard
              title="近 7 日新增账号"
              :bordered="false"
            >
              <div
                ref="accountTrendRef"
                class="chart-box"
              />
            </NCard>

            <NCard
              title="近 7 日审计量"
              :bordered="false"
            >
              <div
                ref="auditTrendRef"
                class="chart-box"
              />
            </NCard>
          </NSpace>
        </NGridItem>

        <NGridItem span="1 m:8">
          <NSpace
            vertical
            :size="16"
            style="width: 100%"
          >
            <NCard
              title="当前账号"
              :bordered="false"
              size="small"
            >
              <NThing>
                <template #avatar>
                  <NAvatar
                    v-if="avatarUrl"
                    round
                    :size="56"
                    :src="avatarUrl"
                    :img-props="avatarImgProps"
                  />
                  <NAvatar
                    v-else
                    round
                    :size="56"
                  >
                    <NovaIcon
                      icon="icon-park-outline:user"
                      :size="28"
                    />
                  </NAvatar>
                </template>
                <template #header>
                  {{ displayName }}
                </template>
                <template #description>
                  {{ authStore.userInfo?.account || '-' }}
                </template>
              </NThing>

              <NSpace
                class="mt-3"
                :size="8"
              >
                <NButton
                  size="small"
                  type="primary"
                  ghost
                  @click="go('/usercenter')"
                >
                  个人中心
                </NButton>
              </NSpace>

              <NDescriptions
                class="mt-3"
                :column="1"
                label-placement="left"
                size="small"
              >
                <NDescriptionsItem label="部门">
                  {{ displayValue(deptText) }}
                </NDescriptionsItem>
                <NDescriptionsItem label="角色">
                  {{ displayValue(roleText) }}
                </NDescriptionsItem>
                <NDescriptionsItem label="用户组">
                  {{ displayValue(groupText) }}
                </NDescriptionsItem>
              </NDescriptions>
            </NCard>

            <NCard
              title="文件类型分布"
              :bordered="false"
              size="small"
            >
              <div
                ref="fileChartRef"
                class="chart-box chart-box--side"
              />
            </NCard>
          </NSpace>
        </NGridItem>
      </NGrid>

      <NAlert
        v-if="state.chartLoadError"
        class="mt-4"
        type="warning"
        :show-icon="false"
      >
        图表运行时加载失败，请刷新页面或重启开发服务。
      </NAlert>
    </n-el>
  </NSpin>
</template>

<style scoped>
.dashboard-page {
  min-height: 100%;
  min-width: 0;
}

.dashboard-banner {
  color: #fff;
  background-color: var(--primary-color);
}

.dashboard-banner :deep(.n-card__content) {
  color: #fff;
}

.dashboard-banner__item {
  min-width: 0;
}

.dashboard-banner__label,
.dashboard-banner__hint {
  opacity: 0.86;
  font-size: 13px;
  line-height: 1.4;
}

.dashboard-banner__value {
  margin: 6px 0 2px;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.15;
  word-break: break-word;
}

.chart-box {
  width: 100%;
  min-width: 0;
  height: 260px;
}

.chart-box--side {
  height: 240px;
}
</style>
