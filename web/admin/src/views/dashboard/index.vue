<!-- Author: Charlie -->

<script setup lang="ts">
import { Chart } from '@antv/g2'
import { dashboardApi } from '@/api'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { NIcon } from 'naive-ui'
import { Icon } from '@iconify/vue/offline'

type ChartInstance = InstanceType<typeof Chart>

const trendChartRef = ref<HTMLDivElement | null>(null)
const fileChartRef = ref<HTMLDivElement | null>(null)
const charts: ChartInstance[] = []
const state = reactive({
  loading: false,
  chartLoadError: false,
  overview: {
    metrics: [] as any[],
    account_trend: [] as any[],
    file_type_share: [] as any[],
  },
})

const metricMeta: Record<string, { icon: string; color: string }> = {
  accounts: { icon: 'icon-park-outline:people', color: '#2563eb' },
  online_sessions: { icon: 'icon-park-outline:connection', color: '#0891b2' },
  files: { icon: 'icon-park-outline:file-code', color: '#0f766e' },
}
const metricTitleMap: Record<string, string> = {
  accounts: '账号',
  online_sessions: '在线设备数',
  files: '文件',
}
const metricHelperMap: Record<string, string> = {
  accounts: '今日新增账号单独统计',
  online_sessions: '当前 Redis 在线令牌数',
  files: '文件数量与存储用量',
}
const metricUnitMap: Record<string, { one: string; other: string }> = {
  accounts: { one: '个账号', other: '个账号' },
  online_sessions: { one: '台设备', other: '台设备' },
  files: { one: '个文件', other: '个文件' },
}
const visibleMetricKeys = new Set(['accounts', 'online_sessions', 'files'])

const metricCards = computed(() =>
  state.overview.metrics
    .filter((item) => visibleMetricKeys.has(item.key))
    .map((item) => {
      const meta = metricMeta[item.key] ?? { icon: 'icon-park-outline:analysis', color: '#64748b' }
      return {
        ...item,
        title: metricTitleMap[item.key] ?? item.key,
        helper: metricHelperMap[item.key] ?? '',
        value: item.value ?? 0,
        unitText: formatMetricUnit(item),
        ...meta,
      }
    }),
)

const trendData = computed(() => [
  ...state.overview.account_trend.map((item) => ({
    ...item,
    type: '新增账号',
  })),
])

onMounted(fetchOverview)

onBeforeUnmount(() => {
  destroyCharts()
})

watch(
  () => [trendData.value, state.overview.file_type_share],
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

function formatMetricUnit(item: any) {
  if (item.key === 'files') {
    return `${formatMetricUnitName(item.value, item.key)} / ${formatFileSize(item.trend_value)}`
  }
  return formatMetricUnitName(item.value, item.key)
}

function formatMetricUnitName(value: number | string | null | undefined, key: string) {
  const count = Number(value ?? 0)
  const unitType = count === 1 ? 'one' : 'other'
  return metricUnitMap[key]?.[unitType] ?? key
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
    await Promise.all([renderTrendChart(), renderFileChart()])
  } catch {
    state.chartLoadError = true
  }
}

function destroyCharts() {
  while (charts.length) {
    charts.pop()?.destroy()
  }
}

async function renderTrendChart() {
  if (!trendChartRef.value) {
    return
  }
  const chart = new Chart({ container: trendChartRef.value, autoFit: true, height: 280 })
  chart.options({
    type: 'line',
    data: trendData.value,
    encode: { x: 'date', y: 'value', color: 'type' },
    scale: { color: { range: ['#2563eb'] } },
    style: { lineWidth: 2.4 },
    axis: { x: { title: false }, y: { title: false, grid: true } },
    legend: { color: { position: 'top' } },
  })
  charts.push(chart)
  await chart.render()
}

async function renderFileChart() {
  if (!fileChartRef.value) {
    return
  }
  const chart = new Chart({ container: fileChartRef.value, autoFit: true, height: 280 })
  chart.options({
    type: 'interval',
    coordinate: { type: 'theta' },
    data: state.overview.file_type_share,
    encode: { y: 'value', color: 'name' },
    transform: [{ type: 'stackY' }],
    legend: { color: { position: 'bottom' } },
    labels: [{ text: 'name', position: 'outside', style: { fontSize: 12 } }],
  })
  charts.push(chart)
  await chart.render()
}
</script>

<template>
  <NSpin :show="state.loading">
    <n-el class="dashboard-page">
      <div class="dashboard-header">
        <div class="min-w-0">
          <h1>运营工作台</h1>
          <p>实时查看账号、在线会话和文件的系统概览。</p>
        </div>
        <NButton text :loading="state.loading" @click="fetchOverview">
          <template #icon>
            <NIcon>
              <Icon icon="icon-park-outline:reload" />
            </NIcon>
          </template>
        </NButton>
      </div>

      <NGrid cols="1 s:2 m:3 xl:3" responsive="screen" :x-gap="16" :y-gap="16">
        <NGridItem v-for="item in metricCards" :key="item.key">
          <NCard class="metric-card" :bordered="false">
            <div class="metric-card__top">
              <span
                class="metric-card__icon"
                :style="{ color: item.color, backgroundColor: `${item.color}14` }"
              >
                <NovaIcon :icon="item.icon" :size="22" />
              </span>
            </div>
            <div class="metric-card__title">
              {{ item.title }}
            </div>
            <div class="metric-card__value">
              <span class="metric-card__number">{{ item.value }}</span>
              <span class="metric-card__unit">{{ item.unitText }}</span>
            </div>
            <div class="metric-card__helper">
              {{ item.helper }}
            </div>
          </NCard>
        </NGridItem>
      </NGrid>

      <NGrid class="mt-4" cols="1 xl:24" responsive="screen" :x-gap="16" :y-gap="16">
        <NGridItem span="1 xl:16">
          <NCard class="dashboard-card" title="最近 7 天" :bordered="false">
            <div ref="trendChartRef" class="chart-box" />
          </NCard>
        </NGridItem>
        <NGridItem span="1 xl:8">
          <NCard class="dashboard-card" title="文件类型" :bordered="false">
            <div ref="fileChartRef" class="chart-box chart-box--small" />
          </NCard>
        </NGridItem>
      </NGrid>

      <NAlert v-if="state.chartLoadError" class="mt-4" type="warning" :show-icon="false">
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

.dashboard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 26px;
  line-height: 1.25;
}

.dashboard-header p {
  margin: 8px 0 0;
  color: var(--text-color-3);
}

.metric-card :deep(.n-card__content) {
  display: grid;
  gap: 10px;
  min-height: 138px;
}

.metric-card__top {
  display: flex;
  align-items: center;
}

.metric-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
}

.metric-card__title,
.metric-card__helper {
  color: var(--text-color-3);
  font-size: 13px;
}

.metric-card__value {
  display: grid;
  gap: 4px;
  color: var(--text-color-base);
  word-break: break-word;
}

.metric-card__number {
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
}

.metric-card__unit {
  min-width: 0;
  color: var(--text-color-3);
  font-size: 13px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.dashboard-card {
  height: 100%;
}

.dashboard-card :deep(.n-card__content) {
  min-width: 0;
  min-height: 290px;
}

.chart-box {
  width: 100%;
  min-width: 0;
  height: 280px;
}

.chart-box--small {
  height: 280px;
}
</style>
