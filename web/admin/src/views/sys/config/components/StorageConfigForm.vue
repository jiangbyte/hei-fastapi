<!-- Author: Charlie -->

<script setup lang="ts">
import { storageConfigApi } from '@/api'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue/offline'
import { onMounted, reactive, ref, computed } from 'vue'
import type { SelectMixedOption } from 'naive-ui/es/select/src/interface'

interface StorageConfig {
  id: string
  name: string
  provider: string
  bucket: string | null
  endpoint: string | null
  access_key: string | null
  secret_key: string | null
  region: string | null
  use_ssl: boolean
  base_url: string | null
  public_path: string
  local_root: string
  is_default: boolean
  remark: string | null
  sort_code: number
}

type ProviderKey = 'local' | 'minio' | 's3' | 'oss'

interface TabState {
  provider: ProviderKey
  label: string
  icon: string
  config: StorageConfig | null
  saving: boolean
}

const emit = defineEmits<{ saved: [] }>()
const message = useMessage()
const loading = ref(false)

const tabs: TabState[] = reactive([
  {
    provider: 'local',
    label: '存储基础配置',
    icon: 'icon-park-outline:computer',
    config: null,
    saving: false,
  },
  {
    provider: 'minio',
    label: 'MinIO',
    icon: 'icon-park-outline:cloud-storage',
    config: null,
    saving: false,
  },
  {
    provider: 's3',
    label: 'Amazon S3',
    icon: 'icon-park-outline:cloud-storage',
    config: null,
    saving: false,
  },
  {
    provider: 'oss',
    label: '阿里云 OSS',
    icon: 'icon-park-outline:cloud-storage',
    config: null,
    saving: false,
  },
])

const activeTab = reactive({ value: 'local' as ProviderKey })

const currentTab = computed(() => tabs.find((t) => t.provider === activeTab.value) ?? tabs[0])

function emptyConfig(p: ProviderKey): StorageConfig {
  return {
    id: '',
    name: '',
    provider: p,
    bucket: '',
    endpoint: '',
    access_key: '',
    secret_key: '',
    region: '',
    use_ssl: false,
    base_url: '',
    public_path: '/api/v1/files',
    local_root: '.runtime/storage',
    is_default: false,
    remark: '',
    sort_code: 0,
  }
}

const localRootOptions: SelectMixedOption[] = [
  { label: '本地运行时目录', value: '.runtime/storage' },
  { label: 'Docker 卷', value: '/app/storage' },
  { label: 'NFS 挂载', value: '/mnt/nfs/storage' },
]

function startCreate(tab: TabState) {
  tab.config = emptyConfig(tab.provider)
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await storageConfigApi.list()
    const all = (res.data ?? []) as StorageConfig[]
    for (const tab of tabs) {
      tab.config = all.find((c) => c.provider === tab.provider) ?? null
    }
    // 默认切换到已启用的 tab
    const defaultTab = tabs.find((t) => t.config?.is_default)
    if (defaultTab) {
      activeTab.value = defaultTab.provider
    }
  } finally {
    loading.value = false
  }
})

async function saveCurrent() {
  const tab = currentTab.value
  tab.saving = true
  try {
    if (tab.config?.id) {
      await storageConfigApi.update(tab.config)
    } else if (tab.config) {
      await storageConfigApi.create(tab.config)
    }
    message.success('保存成功')
    await refreshTab()
    emit('saved')
  } finally {
    tab.saving = false
  }
}

async function setAsDefault() {
  if (!currentTab.value.config?.id) return
  await storageConfigApi.setDefault({ id: currentTab.value.config.id })
  message.success('已设为默认')
  await refreshTab()
  emit('saved')
}

async function refreshTab() {
  const res = await storageConfigApi.list()
  const all = (res.data ?? []) as StorageConfig[]
  for (const tab of tabs) {
    tab.config = all.find((c) => c.provider === tab.provider) ?? null
  }
}
</script>

<template>
  <NSpin :show="loading">
    <div class="storage-tabs-wrapper">
      <NTabs
        v-model:value="activeTab.value"
        type="card"
        placement="left"
        animated
        :style="{ minHeight: '520px' }"
      >
        <NTabPane v-for="tab in tabs" :key="tab.provider" :name="tab.provider" :tab="tab.label">
          <template #tab>
            <span>
              <NIcon size="16" style="margin-right: 4px; vertical-align: -3px">
                <Icon :icon="tab.icon" />
              </NIcon>
              {{ tab.label }}
            </span>
            <NIcon
              v-if="tab.config?.is_default"
              size="16"
              style="margin-left: 4px; vertical-align: -2px; color: var(--primary-color)"
            >
              <Icon icon="icon-park-outline:check" />
            </NIcon>
          </template>

          <div class="form-area">
            <div class="form-actions">
              <NSpace>
                <NButton
                  size="small"
                  :disabled="!tab.config || tab.config.is_default"
                  @click="setAsDefault"
                >
                  设为默认
                </NButton>
                <NButton v-if="!tab.config" type="primary" size="small" @click="startCreate(tab)">
                  创建配置
                </NButton>
                <NButton
                  v-else
                  type="primary"
                  size="small"
                  :loading="tab.saving"
                  @click="saveCurrent"
                >
                  保存
                </NButton>
              </NSpace>
            </div>

            <NForm v-if="tab.config" :key="tab.provider" label-placement="top" class="mt-16px">
              <NGrid :cols="24" :x-gap="24" :y-gap="0">
                <NGi :span="12">
                  <NFormItem label="配置名称">
                    <NInput v-model:value="tab.config.name" />
                  </NFormItem>
                </NGi>

                <NGi :span="12">
                  <NFormItem label="公开访问路径">
                    <NInput v-model:value="tab.config.public_path" />
                  </NFormItem>
                </NGi>

                <!-- ============== 存储基础配置 ============== -->
                <template v-if="tab.provider === 'local'">
                  <NGi :span="24">
                    <NFormItem label="存储根目录">
                      <NSelect
                        v-model:value="tab.config.local_root"
                        :options="localRootOptions"
                        tag
                      />
                    </NFormItem>
                  </NGi>
                </template>

                <!-- ============== 云存储 ============== -->
                <template v-if="tab.provider !== 'local'">
                  <NGi :span="10">
                    <NFormItem label="存储桶">
                      <NInput v-model:value="tab.config.bucket" placeholder="如：my-bucket" />
                    </NFormItem>
                  </NGi>
                  <NGi :span="14">
                    <NFormItem label="服务端点">
                      <NInput
                        v-model:value="tab.config.endpoint"
                        :placeholder="
                          tab.provider === 's3'
                            ? 'https://s3.amazonaws.com'
                            : tab.provider === 'oss'
                              ? 'https://oss-cn-hangzhou.aliyuncs.com'
                              : 'http://localhost:9000'
                        "
                      />
                    </NFormItem>
                  </NGi>
                  <NGi :span="12">
                    <NFormItem :label="tab.provider === 'oss' ? 'AccessKey ID' : 'Access Key'">
                      <NInput
                        v-model:value="tab.config.access_key"
                        type="password"
                        show-password-on="click"
                      />
                    </NFormItem>
                  </NGi>
                  <NGi :span="12">
                    <NFormItem :label="tab.provider === 'oss' ? 'AccessKey Secret' : 'Secret Key'">
                      <NInput
                        v-model:value="tab.config.secret_key"
                        type="password"
                        show-password-on="click"
                      />
                    </NFormItem>
                  </NGi>
                  <NGi :span="8">
                    <NFormItem label="区域">
                      <NInput
                        v-model:value="tab.config.region"
                        :placeholder="
                          tab.provider === 's3'
                            ? 'us-east-1'
                            : tab.provider === 'oss'
                              ? 'cn-hangzhou'
                              : 'us-east-1'
                        "
                      />
                    </NFormItem>
                  </NGi>
                  <NGi :span="8">
                    <NFormItem label="SSL 连接">
                      <NSwitch v-model:value="tab.config.use_ssl" />
                    </NFormItem>
                  </NGi>
                  <NGi :span="8">
                    <NFormItem label="自定义基础 URL">
                      <NInput
                        v-model:value="tab.config.base_url"
                        placeholder="留空则使用服务端点"
                      />
                    </NFormItem>
                  </NGi>
                </template>
              </NGrid>
            </NForm>

            <NEmpty v-else description="暂未配置，点击上方按钮创建" class="mt-32px" />
          </div>
        </NTabPane>
      </NTabs>
    </div>
  </NSpin>
</template>

<style scoped>
.storage-tabs-wrapper {
  min-height: 400px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}
:deep(.n-tabs-tab) {
  min-width: 140px;
}
.mt-16px {
  margin-top: 16px;
}
.mt-32px {
  margin-top: 32px;
}
</style>
