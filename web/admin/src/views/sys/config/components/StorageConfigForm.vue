<!-- Author: Charlie -->

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { onMounted, reactive } from 'vue'
import ConfigSectionLayout from './ConfigSectionLayout.vue'
import { FILES_PUBLIC_PATH } from '@/constants/api'
import { loadByCategory, parseBool, saveByKeys, toBoolStr } from '../composables/useConfigForm'

const CATEGORY = 'STORAGE'
type Engine = 'LOCAL' | 'ALIYUN' | 'TENCENT' | 'MINIO'

const engineOptions = [
  { label: '本地文件', value: 'LOCAL' as Engine },
  { label: '阿里云 OSS', value: 'ALIYUN' as Engine },
  { label: '腾讯云 COS', value: 'TENCENT' as Engine },
  { label: 'MinIO', value: 'MINIO' as Engine },
]

const emit = defineEmits<{ saved: [] }>()
const message = useMessage()

const state = reactive({
  loading: false,
  saving: false,
  subTab: 'LOCAL' as Engine,
  defaultEngine: 'MINIO' as Engine,
  local: {
    localRoot: '/defaultUploadFolder',
    windowsRoot: 'D:/defaultUploadFolder',
    publicPath: FILES_PUBLIC_PATH,
    baseUrl: '',
  },
  aliyun: {
    accessKey: '',
    secretKey: '',
    accessKeySet: false,
    secretKeySet: false,
    endpoint: 'oss-cn-hangzhou.aliyuncs.com',
    bucket: 'defaultbucket',
    region: 'cn-hangzhou',
    useSsl: true,
    baseUrl: '',
    publicPath: FILES_PUBLIC_PATH,
  },
  tencent: {
    accessKey: '',
    secretKey: '',
    accessKeySet: false,
    secretKeySet: false,
    endpoint: '',
    bucket: 'defaultbucket',
    region: 'ap-beijing',
    useSsl: true,
    baseUrl: '',
    publicPath: FILES_PUBLIC_PATH,
  },
  minio: {
    accessKey: '',
    secretKey: '',
    accessKeySet: false,
    secretKeySet: false,
    endpoint: 'https://play.min.io',
    bucket: 'defaultbucket',
    region: '',
    useSsl: false,
    baseUrl: '',
    publicPath: FILES_PUBLIC_PATH,
  },
  snapshot: '',
})

onMounted(() => {
  void reload()
})

async function reload() {
  state.loading = true
  try {
    const map = await loadByCategory(CATEGORY)
    state.defaultEngine = (map.DEFAULT_FILE_ENGINE || 'MINIO') as Engine
    state.local.localRoot = map.STORAGE_LOCAL_LOCAL_ROOT || state.local.localRoot
    state.local.windowsRoot = map.STORAGE_LOCAL_WINDOWS_ROOT || state.local.windowsRoot
    state.local.publicPath = map.STORAGE_LOCAL_PUBLIC_PATH || state.local.publicPath
    state.local.baseUrl = map.STORAGE_LOCAL_BASE_URL || ''

    state.aliyun.accessKey = ''
    state.aliyun.secretKey = ''
    state.aliyun.accessKeySet = parseBool(map.STORAGE_ALIYUN_ACCESS_KEY_SET)
    state.aliyun.secretKeySet = parseBool(map.STORAGE_ALIYUN_SECRET_KEY_SET)
    state.aliyun.endpoint = map.STORAGE_ALIYUN_ENDPOINT || state.aliyun.endpoint
    state.aliyun.bucket = map.STORAGE_ALIYUN_BUCKET || state.aliyun.bucket
    state.aliyun.region = map.STORAGE_ALIYUN_REGION || state.aliyun.region
    state.aliyun.useSsl = map.STORAGE_ALIYUN_USE_SSL
      ? parseBool(map.STORAGE_ALIYUN_USE_SSL)
      : state.aliyun.useSsl
    state.aliyun.baseUrl = map.STORAGE_ALIYUN_BASE_URL || ''
    state.aliyun.publicPath = map.STORAGE_ALIYUN_PUBLIC_PATH || state.aliyun.publicPath

    state.tencent.accessKey = ''
    state.tencent.secretKey = ''
    state.tencent.accessKeySet = parseBool(map.STORAGE_TENCENT_ACCESS_KEY_SET)
    state.tencent.secretKeySet = parseBool(map.STORAGE_TENCENT_SECRET_KEY_SET)
    state.tencent.endpoint = map.STORAGE_TENCENT_ENDPOINT || ''
    state.tencent.bucket = map.STORAGE_TENCENT_BUCKET || state.tencent.bucket
    state.tencent.region = map.STORAGE_TENCENT_REGION || state.tencent.region
    state.tencent.useSsl = map.STORAGE_TENCENT_USE_SSL
      ? parseBool(map.STORAGE_TENCENT_USE_SSL)
      : state.tencent.useSsl
    state.tencent.baseUrl = map.STORAGE_TENCENT_BASE_URL || ''
    state.tencent.publicPath = map.STORAGE_TENCENT_PUBLIC_PATH || state.tencent.publicPath

    state.minio.accessKey = ''
    state.minio.secretKey = ''
    state.minio.accessKeySet = parseBool(map.STORAGE_MINIO_ACCESS_KEY_SET)
    state.minio.secretKeySet = parseBool(map.STORAGE_MINIO_SECRET_KEY_SET)
    state.minio.endpoint = map.STORAGE_MINIO_ENDPOINT || state.minio.endpoint
    state.minio.bucket = map.STORAGE_MINIO_BUCKET || state.minio.bucket
    state.minio.region = map.STORAGE_MINIO_REGION || ''
    state.minio.useSsl = map.STORAGE_MINIO_USE_SSL
      ? parseBool(map.STORAGE_MINIO_USE_SSL)
      : state.minio.useSsl
    state.minio.baseUrl = map.STORAGE_MINIO_BASE_URL || ''
    state.minio.publicPath = map.STORAGE_MINIO_PUBLIC_PATH || state.minio.publicPath

    if (engineOptions.some((o) => o.value === state.defaultEngine)) {
      state.subTab = state.defaultEngine
    }
    state.snapshot = JSON.stringify({
      defaultEngine: state.defaultEngine,
      local: state.local,
      aliyun: state.aliyun,
      tencent: state.tencent,
      minio: state.minio,
    })
  } finally {
    state.loading = false
  }
}

function reset() {
  if (!state.snapshot) return
  const data = JSON.parse(state.snapshot)
  state.defaultEngine = data.defaultEngine
  Object.assign(state.local, data.local)
  Object.assign(state.aliyun, data.aliyun)
  Object.assign(state.tencent, data.tencent)
  Object.assign(state.minio, data.minio)
}

async function save() {
  state.saving = true
  try {
    await saveByKeys([
      {
        config_key: 'DEFAULT_FILE_ENGINE',
        config_value: state.defaultEngine,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_LOCAL_LOCAL_ROOT',
        config_value: state.local.localRoot,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_LOCAL_WINDOWS_ROOT',
        config_value: state.local.windowsRoot,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_LOCAL_PUBLIC_PATH',
        config_value: state.local.publicPath,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_LOCAL_BASE_URL',
        config_value: state.local.baseUrl,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_ACCESS_KEY',
        config_value: state.aliyun.accessKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_SECRET_KEY',
        config_value: state.aliyun.secretKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_ENDPOINT',
        config_value: state.aliyun.endpoint,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_BUCKET',
        config_value: state.aliyun.bucket,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_REGION',
        config_value: state.aliyun.region,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_USE_SSL',
        config_value: toBoolStr(state.aliyun.useSsl),
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_BASE_URL',
        config_value: state.aliyun.baseUrl,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_ALIYUN_PUBLIC_PATH',
        config_value: state.aliyun.publicPath,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_ACCESS_KEY',
        config_value: state.tencent.accessKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_SECRET_KEY',
        config_value: state.tencent.secretKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_ENDPOINT',
        config_value: state.tencent.endpoint,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_BUCKET',
        config_value: state.tencent.bucket,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_REGION',
        config_value: state.tencent.region,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_USE_SSL',
        config_value: toBoolStr(state.tencent.useSsl),
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_BASE_URL',
        config_value: state.tencent.baseUrl,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_TENCENT_PUBLIC_PATH',
        config_value: state.tencent.publicPath,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_ACCESS_KEY',
        config_value: state.minio.accessKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_SECRET_KEY',
        config_value: state.minio.secretKey,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_ENDPOINT',
        config_value: state.minio.endpoint,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_BUCKET',
        config_value: state.minio.bucket,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_REGION',
        config_value: state.minio.region,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_USE_SSL',
        config_value: toBoolStr(state.minio.useSsl),
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_BASE_URL',
        config_value: state.minio.baseUrl,
        category: CATEGORY,
      },
      {
        config_key: 'STORAGE_MINIO_PUBLIC_PATH',
        config_value: state.minio.publicPath,
        category: CATEGORY,
      },
    ])
    message.success('保存成功')
    await reload()
    emit('saved')
  } finally {
    state.saving = false
  }
}
</script>

<template>
  <NSpin :show="state.loading">
    <NForm
      class="sys-config-form mb-12px"
      label-placement="top"
    >
      <NFormItem label="默认文件存储">
        <NRadioGroup v-model:value="state.defaultEngine">
          <NSpace>
            <NRadio
              v-for="opt in engineOptions"
              :key="opt.value"
              :value="opt.value"
              :label="opt.label"
            />
          </NSpace>
        </NRadioGroup>
      </NFormItem>
    </NForm>

    <NTabs
      v-model:value="state.subTab"
      type="line"
      class="sys-config-subnav"
    >
      <NTab
        v-for="opt in engineOptions"
        :key="opt.value"
        :name="opt.value"
        :tab="opt.label"
      />
    </NTabs>

    <ConfigSectionLayout
      description="配置各文件存储引擎参数。上方单选切换默认引擎（互斥）；保存后热重载生效。"
      :saving="state.saving"
      @save="save"
      @reset="reset"
    >
      <NForm
        class="sys-config-form"
        label-placement="left"
        label-width="140"
        require-mark-placement="left"
      >
        <template v-if="state.subTab === 'LOCAL'">
          <NFormItem
            label="WINDOWS存储位置"
            required
          >
            <NInput
              v-model:value="state.local.windowsRoot"
              placeholder="D:/defaultUploadFolder"
            />
          </NFormItem>
          <NFormItem
            label="LINUX存储位置"
            required
          >
            <NInput
              v-model:value="state.local.localRoot"
              placeholder="/defaultUploadFolder"
            />
          </NFormItem>
        </template>

        <template v-else-if="state.subTab === 'ALIYUN'">
          <NFormItem
            label="阿里云密钥ID"
            required
          >
            <NInput
              v-model:value="state.aliyun.accessKey"
              :placeholder="
                state.aliyun.accessKeySet ? '已配置，留空不修改' : '阿里云文件 AccessKeyId'
              "
            />
          </NFormItem>
          <NFormItem
            label="阿里云密钥SECRET"
            required
          >
            <NInput
              v-model:value="state.aliyun.secretKey"
              type="password"
              show-password-on="click"
              :placeholder="
                state.aliyun.secretKeySet ? '已配置，留空不修改' : '阿里云文件 AccessKeySecret'
              "
            />
          </NFormItem>
          <NFormItem
            label="阿里云文件端点"
            required
          >
            <NInput
              v-model:value="state.aliyun.endpoint"
              placeholder="oss-cn-hangzhou.aliyuncs.com"
            />
          </NFormItem>
          <NFormItem
            label="阿里云默认储存桶"
            required
          >
            <NInput
              v-model:value="state.aliyun.bucket"
              placeholder="defaultbucket"
            />
          </NFormItem>
        </template>

        <template v-else-if="state.subTab === 'TENCENT'">
          <NFormItem
            label="腾讯云密钥ID"
            required
          >
            <NInput
              v-model:value="state.tencent.accessKey"
              :placeholder="
                state.tencent.accessKeySet ? '已配置，留空不修改' : '腾讯云文件 SecretId'
              "
            />
          </NFormItem>
          <NFormItem
            label="腾讯云密钥SECRET"
            required
          >
            <NInput
              v-model:value="state.tencent.secretKey"
              type="password"
              show-password-on="click"
              :placeholder="
                state.tencent.secretKeySet ? '已配置，留空不修改' : '腾讯云文件 SecretKey'
              "
            />
          </NFormItem>
          <NFormItem
            label="腾讯云区域ID"
            required
          >
            <NInput
              v-model:value="state.tencent.region"
              placeholder="ap-beijing"
            />
          </NFormItem>
          <NFormItem
            label="腾讯云存储桶"
            required
          >
            <NInput
              v-model:value="state.tencent.bucket"
              placeholder="defaultbucket"
            />
          </NFormItem>
        </template>

        <template v-else>
          <NFormItem
            label="MINIO通道KEY"
            required
          >
            <NInput
              v-model:value="state.minio.accessKey"
              :placeholder="state.minio.accessKeySet ? '已配置，留空不修改' : 'MINIO Access Key'"
            />
          </NFormItem>
          <NFormItem
            label="MINIO密钥KEY"
            required
          >
            <NInput
              v-model:value="state.minio.secretKey"
              type="password"
              show-password-on="click"
              :placeholder="state.minio.secretKeySet ? '已配置，留空不修改' : 'MINIO Secret Key'"
            />
          </NFormItem>
          <NFormItem
            label="MINIO端点"
            required
          >
            <NInput
              v-model:value="state.minio.endpoint"
              placeholder="https://play.min.io"
            />
          </NFormItem>
          <NFormItem
            label="MINIO存储桶"
            required
          >
            <NInput
              v-model:value="state.minio.bucket"
              placeholder="defaultbucket"
            />
          </NFormItem>
        </template>
      </NForm>
    </ConfigSectionLayout>
  </NSpin>
</template>

<style scoped>
.mb-12px {
  margin-bottom: 12px;
}
</style>
