<!-- Author: Charlie -->

<script setup lang="ts">
import { accountApi } from '@/api'
import { createTagColor, displayValue, formatDateTime, resolveFileUrl } from '@/utils'
import { computed, reactive } from 'vue'
import { dictTypeData, dictTypeColor } from '@/utils/dict'

const state = reactive({
  showModal: false,
  loading: false,
  account: {} as any,
})

const avatarAlt = computed(() => state.account?.nickname || '账号 avatar')
const avatarUrl = computed(() => resolveFileUrl(state.account?.avatar))
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

async function openModal(id: string) {
  state.account = {}
  state.showModal = true
  await fetchDetail(id)
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const response = await accountApi.detail({ id })
    state.account = response.data ?? {}
  } finally {
    state.loading = false
  }
}

defineExpose({
  openModal,
})
</script>

<template>
  <NModal
    v-model:show="state.showModal"
    preset="card"
    draggable
    :mask-closable="false"
    :title="'账号详情'"
    style="width: 680px"
  >
    <NScrollbar class="h-[480px] pr-16px">
      <NSpin :show="state.loading">
        <NTabs type="line" animated>
          <NTabPane name="account" :tab="'账号信息'">
            <NDescriptions label-placement="left" bordered :column="1">
              <NDescriptionsItem :label="'账号 ID'">
                {{ displayValue(state.account.id) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'账号类型'">
                <NTag
                  :color="createTagColor(dictTypeColor('ACCOUNT_TYPE', state.account.account_type))"
                  :bordered="false"
                >
                  {{ dictTypeData('ACCOUNT_TYPE', state.account.account_type) }}
                </NTag>
              </NDescriptionsItem>
              <NDescriptionsItem :label="'账号状态'">
                <NTag
                  :color="
                    createTagColor(dictTypeColor('ACCOUNT_STATUS', state.account.account_status))
                  "
                  :bordered="false"
                >
                  {{ dictTypeData('ACCOUNT_STATUS', state.account.account_status) }}
                </NTag>
              </NDescriptionsItem>
              <NDescriptionsItem :label="'注销时间'">
                {{ formatDateTime(state.account.cancelled_at) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'注销人'">
                {{ displayValue(state.account.cancelled_by) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'注销原因'">
                {{ displayValue(state.account.cancel_reason) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'上次登录IP'">
                {{ displayValue(state.account.last_login_ip) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'上次登录地址'">
                {{ displayValue(state.account.last_login_address) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'上次登录时间'">
                {{ formatDateTime(state.account.last_login_time) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'上次登录设备'">
                {{ displayValue(state.account.last_login_device) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'最近登录IP'">
                {{ displayValue(state.account.latest_login_ip) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'最近登录地址'">
                {{ displayValue(state.account.latest_login_address) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'最近登录时间'">
                {{ formatDateTime(state.account.latest_login_time) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'最近登录设备'">
                {{ displayValue(state.account.latest_login_device) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'创建时间'">
                {{ formatDateTime(state.account.created_at) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'更新时间'">
                {{ formatDateTime(state.account.updated_at) }}
              </NDescriptionsItem>
            </NDescriptions>
          </NTabPane>

          <NTabPane name="identity" :tab="'登录身份'">
            <NDescriptions label-placement="left" bordered :column="1">
              <NDescriptionsItem :label="'账号'">
                {{ displayValue(state.account.account) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'邮箱登录身份'">
                {{ displayValue(state.account.email_identity) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'邮箱登录 启用'">
                {{ state.account.email_login_enabled ? '是' : '否' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'邮箱已验证'">
                {{ state.account.email_identity_verified ? '是' : '否' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'邮箱绑定状态'">
                {{
                  dictTypeData(
                    'ACCOUNT_IDENTITY_BIND_STATUS',
                    state.account.email_identity_bind_status,
                  ) || displayValue(state.account.email_identity_bind_status)
                }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'手机号登录身份'">
                {{ displayValue(state.account.phone_identity) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'手机号登录 启用'">
                {{ state.account.phone_login_enabled ? '是' : '否' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'手机号已验证'">
                {{ state.account.phone_identity_verified ? '是' : '否' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'手机号绑定状态'">
                {{
                  dictTypeData(
                    'ACCOUNT_IDENTITY_BIND_STATUS',
                    state.account.phone_identity_bind_status,
                  ) || displayValue(state.account.phone_identity_bind_status)
                }}
              </NDescriptionsItem>
            </NDescriptions>
          </NTabPane>

          <NTabPane name="profile" :tab="'用户资料'">
            <NDescriptions label-placement="left" bordered :column="1">
              <NDescriptionsItem :label="'名称'">
                {{ displayValue(state.account.name) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'昵称'">
                {{ displayValue(state.account.nickname) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'头像'">
                <NAvatar
                  v-if="avatarUrl"
                  :src="avatarUrl"
                  :alt="avatarAlt"
                  :img-props="avatarImgProps"
                />
                <template v-else> - </template>
              </NDescriptionsItem>
              <NDescriptionsItem :label="'签名'">
                {{ displayValue(state.account.signature) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'手机号'">
                {{ displayValue(state.account.phone) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'邮箱'">
                {{ displayValue(state.account.email) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'等级'">
                {{ displayValue(state.account.level) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'简介'">
                {{ displayValue(state.account.bio) }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'备注'">
                {{ displayValue(state.account.remark) }}
              </NDescriptionsItem>
            </NDescriptions>
          </NTabPane>
        </NTabs>
      </NSpin>
    </NScrollbar>
  </NModal>
</template>
