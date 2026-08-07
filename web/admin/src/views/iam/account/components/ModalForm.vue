<!-- Author: Charlie -->

<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import ImageUpload from '@/components/upload/ImageUpload.vue'
import { accountApi } from '@/api'
import { createRequiredRule, isValidEmail, toNullableString } from '@/utils'
import { dictList } from '@/utils/dict'
import { encryptPasswords } from '@/utils/security'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits<{
  saved: []
}>()

const formRef = ref<FormInst | null>(null)
const defaultFormData = {
  account: '',
  password: '',
  account_type: 'PORTAL',
  account_status: 'ENABLED',
  name: '',
  nickname: '',
  avatar: '',
  signature: '',
  phone: '',
  email: '',
  email_login_enabled: false,
  phone_login_enabled: false,
  email_identity: '',
  phone_identity: '',
  email_identity_verified: false,
  phone_identity_verified: false,
  email_identity_bind_status: 'BOUND',
  phone_identity_bind_status: 'BOUND',
  bio: '',
  level: '',
  remark: '',
}
const state = reactive({
  showModal: false,
  loading: false,
  submitLoading: false,
  dataId: null as string | null,
  formModel: { ...defaultFormData },
})

const accountStatusOptions = computed(() =>
  dictList('ACCOUNT_STATUS').filter((o: any) => !o.value.includes('CANCELLED')),
)

const modalTitle = computed(() => (state.dataId ? '编辑账号' : '新增账号'))

function validateEmailIdentity(_rule: FormItemRule, value: string) {
  const text = String(value ?? '').trim()
  if (!text) {
    return state.formModel.email_login_enabled ? new Error('请输入邮箱') : true
  }
  if (!isValidEmail(text)) {
    return new Error('请输入有效邮箱')
  }
  return true
}

const rules = computed<FormRules>(() => ({
  account: createRequiredRule('账号', 'input'),
  password: [
    {
      validator: (_rule, value) => {
        if (!state.dataId && !String(value ?? '').trim()) {
          return new Error('请输入密码')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  account_type: createRequiredRule('账号类型', 'change'),
  account_status: createRequiredRule('账号状态', 'change'),
  email: [
    {
      validator: validateEmailIdentity,
      trigger: ['input', 'blur'],
    },
  ],
}))

async function openModal(id?: string) {
  state.dataId = id ?? null
  state.formModel = { ...defaultFormData }
  state.showModal = true

  if (id) {
    await fetchDetail(id)
  }
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const response = await accountApi.detail({ id })
    state.formModel = Object.assign({}, defaultFormData, response.data, {
      password: '',
      nickname: response.data?.nickname ?? '',
      avatar: response.data?.avatar ?? '',
      signature: response.data?.signature ?? '',
      phone: response.data?.phone ?? '',
      email: response.data?.email ?? '',
      email_login_enabled: Boolean(response.data?.email_login_enabled),
      phone_login_enabled: Boolean(response.data?.phone_login_enabled),
      email_identity: response.data?.email_identity ?? '',
      phone_identity: response.data?.phone_identity ?? '',
      email_identity_verified: Boolean(response.data?.email_identity_verified),
      phone_identity_verified: Boolean(response.data?.phone_identity_verified),
      email_identity_bind_status: response.data?.email_identity_bind_status ?? 'BOUND',
      phone_identity_bind_status: response.data?.phone_identity_bind_status ?? 'BOUND',
      bio: response.data?.bio ?? '',
      level: response.data?.level ?? '',
      remark: response.data?.remark ?? '',
    })
  } finally {
    state.loading = false
  }
}

function closeModal() {
  state.showModal = false
  state.submitLoading = false
}

async function submitForm() {
  await formRef.value?.validate()
  state.submitLoading = true
  try {
    const payload: any = {
      ...state.formModel,
      account: state.formModel.account.trim(),
      password: toNullableString(state.formModel.password),
      name: state.formModel.name.trim(),
      nickname: toNullableString(state.formModel.nickname),
      avatar: toNullableString(state.formModel.avatar),
      signature: toNullableString(state.formModel.signature),
      phone: toNullableString(state.formModel.phone),
      email: toNullableString(state.formModel.email),
      email_login_enabled: Boolean(state.formModel.email_login_enabled),
      phone_login_enabled: Boolean(state.formModel.phone_login_enabled),
      email_identity: state.formModel.email_login_enabled
        ? toNullableString(state.formModel.email)
        : null,
      phone_identity: state.formModel.phone_login_enabled
        ? toNullableString(state.formModel.phone)
        : null,
      email_identity_verified: Boolean(state.formModel.email_login_enabled),
      phone_identity_verified: Boolean(state.formModel.phone_login_enabled),
      email_identity_bind_status: 'BOUND',
      phone_identity_bind_status: 'BOUND',
      bio: toNullableString(state.formModel.bio),
      level: toNullableString(state.formModel.level),
      remark: toNullableString(state.formModel.remark),
    }
    if (payload.password) {
      const encrypted = await encryptPasswords({ password: payload.password })
      payload.password = encrypted.values.password
      payload.password_key_id = encrypted.password_key_id
    } else {
      payload.password_key_id = null
    }
    if (payload.account_type === 'ADMIN') {
      payload.bio = null
      payload.level = null
    } else {
      payload.remark = null
    }

    if (state.dataId) {
      await accountApi.update({
        ...payload,
        id: state.dataId,
      })
      window.$message.success('更新成功')
    } else {
      await accountApi.create(payload)
      window.$message.success('创建成功')
    }

    closeModal()
    emit('saved')
  } finally {
    state.submitLoading = false
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
    :title="modalTitle"
    style="width: 720px"
    :segmented="{ content: true, action: true }"
  >
    <NSpin :show="state.loading">
      <NScrollbar class="h-[480px] pr-16px">
        <NForm
          ref="formRef"
          :model="state.formModel"
          :rules="rules"
          label-placement="left"
          label-width="110"
          :disabled="state.loading || state.submitLoading"
        >
          <NTabs type="line" animated>
            <NTabPane name="account" :tab="'账号信息'">
              <NFormItem :label="'密码'" path="password">
                <NInput
                  v-model:value="state.formModel.password"
                  type="password"
                  show-password-on="click"
                  :placeholder="state.dataId ? '留空则保持当前密码' : undefined"
                />
              </NFormItem>
              <PasswordStrengthBar :password="state.formModel.password" />
              <NFormItem :label="'账号类型'" path="account_type">
                <DictSelect
                  v-model="state.formModel.account_type"
                  dict-code="ACCOUNT_TYPE"
                  :disabled="!!state.dataId"
                />
              </NFormItem>
              <NFormItem :label="'账号状态'" path="account_status">
                <NRadioGroup v-model:value="state.formModel.account_status">
                  <NRadio
                    v-for="option in accountStatusOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </NRadio>
                </NRadioGroup>
              </NFormItem>
            </NTabPane>

            <NTabPane name="identity" :tab="'登录身份'">
              <NFormItem :label="'账号'" path="account">
                <NInput v-model:value="state.formModel.account" />
              </NFormItem>
              <NFormItem :label="'邮箱'" path="email">
                <NInput v-model:value="state.formModel.email" />
              </NFormItem>
              <NFormItem :label="'启用邮箱登录'">
                <NSwitch v-model:value="state.formModel.email_login_enabled" />
              </NFormItem>
              <NFormItem :label="'手机号'" path="phone">
                <NInput v-model:value="state.formModel.phone" />
              </NFormItem>
              <NFormItem :label="'启用手机号登录'">
                <NSwitch v-model:value="state.formModel.phone_login_enabled" />
              </NFormItem>
            </NTabPane>

            <NTabPane name="profile" :tab="'用户资料'">
              <NFormItem :label="'名称'" path="name">
                <NInput v-model:value="state.formModel.name" />
              </NFormItem>
              <NFormItem :label="'昵称'" path="nickname">
                <NInput v-model:value="state.formModel.nickname" />
              </NFormItem>
              <NFormItem :label="'头像'" path="avatar">
                <ImageUpload v-model:value="state.formModel.avatar" />
              </NFormItem>
              <NFormItem :label="'签名'" path="signature">
                <NInput
                  v-model:value="state.formModel.signature"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
              <NFormItem
                v-if="state.formModel.account_type === 'ADMIN'"
                :label="'个性签名'"
                path="signature"
              >
                <NInput
                  v-model:value="state.formModel.signature"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
              <NFormItem
                v-if="state.formModel.account_type === 'PORTAL'"
                :label="'等级'"
                path="level"
              >
                <NInput v-model:value="state.formModel.level" />
              </NFormItem>
              <NFormItem
                v-if="state.formModel.account_type === 'PORTAL'"
                :label="'简介'"
                path="bio"
              >
                <NInput
                  v-model:value="state.formModel.bio"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
              <NFormItem
                v-if="state.formModel.account_type === 'ADMIN'"
                :label="'备注'"
                path="remark"
              >
                <NInput
                  v-model:value="state.formModel.remark"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
            </NTabPane>
          </NTabs>
        </NForm>
      </NScrollbar>
    </NSpin>

    <template #action>
      <NSpace justify="end" align="center">
        <NButton @click="closeModal"> 取消 </NButton>
        <NButton type="primary" :loading="state.submitLoading" @click="submitForm"> 确认 </NButton>
      </NSpace>
    </template>
  </NModal>
</template>
