<!-- Author: Charlie -->

<script setup lang="ts">
import { configApi } from '@/api'
import { onMounted, reactive } from 'vue'

interface Item {
  id: string
  config_key: string
  config_value: string
  remark: string
}

const props = defineProps<{ category: string }>()
const emit = defineEmits<{ saved: [] }>()

const fields = reactive({
  enabled: { id: '', value: false, remark: '' },
  webhookUrl: { id: '', value: '', remark: '' },
  webhookSecret: { id: '', value: '', remark: '' },
  analysisInterval: { id: '', value: 300, remark: '' },
  cooldown: { id: '', value: 1800, remark: '' },
  ruleBruteForce: { id: '', value: true, remark: '' },
  ruleUnusualHours: { id: '', value: true, remark: '' },
  ruleSensitiveOps: { id: '', value: true, remark: '' },
  ruleBulkDelete: { id: '', value: true, remark: '' },
  ruleIpAnomaly: { id: '', value: true, remark: '' },
  bruteForceThreshold: { id: '', value: 10, remark: '' },
  bulkDeleteThreshold: { id: '', value: 20, remark: '' },
  ipAnomalyThreshold: { id: '', value: 3, remark: '' },
  saving: false,
  testingWebhook: false,
})

onMounted(async () => {
  const res = await configApi.list({ category: props.category })
  for (const row of (res.data ?? []) as Item[]) {
    switch (row.config_key) {
      case 'audit_alert.enabled':
        fields.enabled = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.webhook_url':
        fields.webhookUrl = { id: row.id, value: row.config_value ?? '', remark: row.remark ?? '' }
        break
      case 'audit_alert.webhook_secret':
        fields.webhookSecret = {
          id: row.id,
          value: row.config_value ?? '',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.analysis_interval_seconds':
        fields.analysisInterval = {
          id: row.id,
          value: Number(row.config_value) || 300,
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.alert_cooldown_seconds':
        fields.cooldown = {
          id: row.id,
          value: Number(row.config_value) || 1800,
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.rule_brute_force':
        fields.ruleBruteForce = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.rule_unusual_hours':
        fields.ruleUnusualHours = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.rule_sensitive_ops':
        fields.ruleSensitiveOps = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.rule_bulk_delete':
        fields.ruleBulkDelete = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.rule_ip_anomaly':
        fields.ruleIpAnomaly = {
          id: row.id,
          value: row.config_value === 'true',
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.brute_force_threshold':
        fields.bruteForceThreshold = {
          id: row.id,
          value: Number(row.config_value) || 10,
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.bulk_delete_threshold':
        fields.bulkDeleteThreshold = {
          id: row.id,
          value: Number(row.config_value) || 20,
          remark: row.remark ?? '',
        }
        break
      case 'audit_alert.ip_anomaly_threshold':
        fields.ipAnomalyThreshold = {
          id: row.id,
          value: Number(row.config_value) || 3,
          remark: row.remark ?? '',
        }
        break
    }
  }
})

async function saveAll() {
  fields.saving = true
  try {
    await configApi.batchSave({
      items: [
        {
          id: fields.enabled.id,
          config_key: 'audit_alert.enabled',
          config_value: String(fields.enabled.value),
        },
        {
          id: fields.webhookUrl.id,
          config_key: 'audit_alert.webhook_url',
          config_value: fields.webhookUrl.value,
        },
        {
          id: fields.webhookSecret.id,
          config_key: 'audit_alert.webhook_secret',
          config_value: fields.webhookSecret.value,
        },
        {
          id: fields.analysisInterval.id,
          config_key: 'audit_alert.analysis_interval_seconds',
          config_value: String(fields.analysisInterval.value),
        },
        {
          id: fields.cooldown.id,
          config_key: 'audit_alert.alert_cooldown_seconds',
          config_value: String(fields.cooldown.value),
        },
        {
          id: fields.ruleBruteForce.id,
          config_key: 'audit_alert.rule_brute_force',
          config_value: String(fields.ruleBruteForce.value),
        },
        {
          id: fields.ruleUnusualHours.id,
          config_key: 'audit_alert.rule_unusual_hours',
          config_value: String(fields.ruleUnusualHours.value),
        },
        {
          id: fields.ruleSensitiveOps.id,
          config_key: 'audit_alert.rule_sensitive_ops',
          config_value: String(fields.ruleSensitiveOps.value),
        },
        {
          id: fields.ruleBulkDelete.id,
          config_key: 'audit_alert.rule_bulk_delete',
          config_value: String(fields.ruleBulkDelete.value),
        },
        {
          id: fields.ruleIpAnomaly.id,
          config_key: 'audit_alert.rule_ip_anomaly',
          config_value: String(fields.ruleIpAnomaly.value),
        },
        {
          id: fields.bruteForceThreshold.id,
          config_key: 'audit_alert.brute_force_threshold',
          config_value: String(fields.bruteForceThreshold.value),
        },
        {
          id: fields.bulkDeleteThreshold.id,
          config_key: 'audit_alert.bulk_delete_threshold',
          config_value: String(fields.bulkDeleteThreshold.value),
        },
        {
          id: fields.ipAnomalyThreshold.id,
          config_key: 'audit_alert.ip_anomaly_threshold',
          config_value: String(fields.ipAnomalyThreshold.value),
        },
      ],
    })
    window.$message.success('保存成功')
    emit('saved')
  } finally {
    fields.saving = false
  }
}

async function testWebhook() {
  const url = fields.webhookUrl.value.trim()
  if (!url) {
    window.$message.warning('请先填写 Webhook URL')
    return
  }
  fields.testingWebhook = true
  try {
    await configApi.testAuditAlertWebhook({
      webhook_url: url,
      webhook_secret: fields.webhookSecret.value,
    })
    window.$message.success('测试消息已发送，请检查 Webhook 接收端')
  } catch {
    window.$message.error('Webhook 测试失败，请检查 URL 和密钥')
  } finally {
    fields.testingWebhook = false
  }
}
</script>

<template>
  <NForm label-placement="top" :label-width="140">
    <NCard title="全局开关" :bordered="false" size="small">
      <NGrid :cols="24" :x-gap="24" :y-gap="12">
        <NGi :span="8">
          <NFormItem label="启用告警" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.enabled.value" />
          </NFormItem>
        </NGi>
        <NGi :span="16">
          <NFormItem label="Webhook URL" :style="{ marginBottom: 0 }">
            <div style="display: flex; gap: 8px; width: 100%">
              <NInput v-model:value="fields.webhookUrl.value" placeholder="飞书 Webhook 地址" />
              <NButton :loading="fields.testingWebhook" size="small" @click="testWebhook">
                测试
              </NButton>
            </div>
          </NFormItem>
          <NFormItem label="Webhook 密钥" :style="{ marginBottom: 0 }">
            <NInput
              v-model:value="fields.webhookSecret.value"
              type="password"
              placeholder="签名密钥(可选)"
            />
          </NFormItem>
        </NGi>
      </NGrid>
    </NCard>

    <NCard title="分析参数" :bordered="false" size="small" class="mt-12px">
      <NGrid :cols="24" :x-gap="24" :y-gap="12">
        <NGi :span="12">
          <NFormItem label="分析周期(秒)" :style="{ marginBottom: 0 }">
            <NInputNumber
              v-model:value="fields.analysisInterval.value"
              class="w-full"
              :min="60"
              :max="3600"
            />
            <div class="hint">
              {{ fields.analysisInterval.remark }}
            </div>
          </NFormItem>
        </NGi>
        <NGi :span="12">
          <NFormItem label="告警冷却(秒)" :style="{ marginBottom: 0 }">
            <NInputNumber
              v-model:value="fields.cooldown.value"
              class="w-full"
              :min="60"
              :max="86400"
            />
            <div class="hint">
              {{ fields.cooldown.remark }}
            </div>
          </NFormItem>
        </NGi>
      </NGrid>
    </NCard>

    <NCard title="告警规则" :bordered="false" size="small" class="mt-12px">
      <NGrid :cols="24" :x-gap="24" :y-gap="12">
        <NGi :span="8">
          <NFormItem label="暴力破解检测" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.ruleBruteForce.value" />
          </NFormItem>
          <div class="mt-4px">
            <span class="hint">阈值: </span>
            <NInputNumber v-model:value="fields.bruteForceThreshold.value" :min="1" :max="100" />
            <span class="hint"> 次/分钟</span>
          </div>
        </NGi>
        <NGi :span="8">
          <NFormItem label="异常时间操作" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.ruleUnusualHours.value" />
          </NFormItem>
          <div class="mt-4px hint">凌晨 0-6 点的角色/权限变更</div>
        </NGi>
        <NGi :span="8">
          <NFormItem label="敏感操作监控" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.ruleSensitiveOps.value" />
          </NFormItem>
          <div class="mt-4px hint">角色授权、权限变更操作</div>
        </NGi>
        <NGi :span="8">
          <NFormItem label="批量删除检测" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.ruleBulkDelete.value" />
          </NFormItem>
          <div class="mt-4px">
            <span class="hint">阈值: </span>
            <NInputNumber v-model:value="fields.bulkDeleteThreshold.value" :min="1" :max="1000" />
            <span class="hint"> 次/5分钟</span>
          </div>
        </NGi>
        <NGi :span="8">
          <NFormItem label="IP 异常检测" :style="{ marginBottom: 0 }">
            <NSwitch v-model:value="fields.ruleIpAnomaly.value" />
          </NFormItem>
          <div class="mt-4px">
            <span class="hint">阈值: </span>
            <NInputNumber v-model:value="fields.ipAnomalyThreshold.value" :min="2" :max="50" />
            <span class="hint"> 个不同 IP/15分钟</span>
          </div>
        </NGi>
      </NGrid>
    </NCard>

    <NButton type="primary" class="mt-16px" :loading="fields.saving" @click="saveAll">
      保存配置
    </NButton>
  </NForm>
</template>

<style scoped>
.hint {
  font-size: 12px;
  color: #aaa;
}
.mt-4px {
  margin-top: 4px;
}
.mt-12px {
  margin-top: 12px;
}
.mt-16px {
  margin-top: 16px;
}
.w-full {
  width: 100%;
}
</style>
