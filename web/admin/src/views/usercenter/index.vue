<!-- Author: Charlie -->

<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores'
import { isValidEmail, resolveFileUrl } from '@/utils'
import { encryptPasswords } from '@/utils/security'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import AvatarUploadModal from './components/AvatarUploadModal.vue'

const authStore = useAuthStore()
const route = useRoute()
const emailFormRef = ref<FormInst | null>(null)
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

const state = reactive({
  loading: false,
  savingProfile: false,
  savingPassword: false,
  savingPhone: false,
  savingEmail: false,
  savingMfa: false,
  activeTab: 'basic_info',
  avatarModalShow: false,
  me: null as any,
  mfa: {
    enabled: false,
    totpEnabled: false,
    required: false,
    setupSecret: '',
    setupUri: '',
    confirmCode: '',
    backupCodes: [] as string[],
    disablePassword: '',
    disableCode: '',
    webauthnCount: 0,
  },
  profileForm: {
    name: '',
    nickname: '',
    avatar: '',
    signature: '',
    remark: '',
  },
  passwordForm: {
    old_password: '',
    new_password: '',
    confirm_password: '',
  },
  phoneForm: {
    phone: '',
    phone_login_enabled: false,
  },
  emailForm: {
    email: '',
    email_login_enabled: false,
  },
  bindConfirm: {
    show: false,
    type: 'phone' as 'phone' | 'email',
    password: '',
    loading: false,
  },
})

const profile = computed(() => state.me?.profile ?? {})
const avatarUrl = computed(() => resolveFileUrl(state.profileForm.avatar))
const displayName = computed(() => state.me?.nickname || '-')
const roleNames = computed(() => mapNames(state.me?.role_id_names))
const deptNames = computed(() => mapNames(state.me?.dept_id_names))
const mainDept = computed(() => deptNames.value || '未设置')
const mainRole = computed(() => roleNames.value || '未设置')
const contactText = computed(() => {
  const parts = [profile.value.phone, profile.value.email].filter(Boolean)
  return parts.length ? parts.join(' / ') : '未设置'
})
const bindConfirmTitle = computed(() =>
  state.bindConfirm.type === 'phone' ? '确认更新手机号' : '确认更新邮箱',
)
const emailRules = computed<FormRules>(() => ({
  email: [
    {
      validator: validateEmailForm,
      trigger: ['input', 'blur'],
    },
  ],
}))

onMounted(async () => {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : ''
  if (tab) {
    state.activeTab = tab
  }
  state.loading = true
  try {
    await loadMe()
    await loadMfaStatus()
  } finally {
    state.loading = false
  }
})

async function loadMfaStatus() {
  try {
    const res = await authApi.mfaStatus()
    state.mfa.enabled = Boolean(res.data?.enabled)
    state.mfa.totpEnabled = Boolean(res.data?.totp_enabled)
    state.mfa.required = Boolean(res.data?.required)
    state.mfa.webauthnCount = Number(res.data?.webauthn_count ?? 0)
  } catch {
    // 接口不可用时忽略
  }
}

async function startMfaSetup() {
  state.savingMfa = true
  try {
    const res = await authApi.mfaSetup()
    state.mfa.setupSecret = res.data?.secret ?? ''
    state.mfa.setupUri = res.data?.otpauth_uri ?? ''
    state.mfa.confirmCode = ''
    state.mfa.backupCodes = []
    window.$message.success('请用认证器扫描或手动录入密钥')
  } finally {
    state.savingMfa = false
  }
}

async function confirmMfaSetup() {
  if (!state.mfa.confirmCode.trim()) {
    window.$message.warning('请输入动态码')
    return
  }
  state.savingMfa = true
  try {
    const res = await authApi.mfaConfirm({ code: state.mfa.confirmCode.trim() })
    state.mfa.backupCodes = res.data?.backup_codes ?? []
    state.mfa.setupSecret = ''
    state.mfa.setupUri = ''
    state.mfa.confirmCode = ''
    await loadMfaStatus()
    window.$message.success('MFA 已启用，请妥善保存备份码')
  } finally {
    state.savingMfa = false
  }
}

async function disableMfa() {
  if (!state.mfa.disablePassword) {
    window.$message.warning('请输入当前密码')
    return
  }
  if (state.mfa.totpEnabled && !state.mfa.disableCode.trim()) {
    window.$message.warning('请输入动态码或备份码')
    return
  }
  state.savingMfa = true
  try {
    const encrypted = await encryptPasswords({ password: state.mfa.disablePassword })
    await authApi.mfaDisable({
      password: encrypted.values.password,
      password_key_id: encrypted.password_key_id,
      code: state.mfa.disableCode.trim() || undefined,
    })
    state.mfa.disablePassword = ''
    state.mfa.disableCode = ''
    state.mfa.backupCodes = []
    await loadMfaStatus()
    window.$message.success('MFA 已关闭')
  } finally {
    state.savingMfa = false
  }
}

function bufferToBase64Url(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function base64UrlToBuffer(value: string) {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/')
  const pad = padded.length % 4 === 0 ? '' : '='.repeat(4 - (padded.length % 4))
  const binary = atob(padded + pad)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}

async function registerWebAuthn() {
  if (!window.PublicKeyCredential) {
    window.$message.warning('当前浏览器不支持 Passkey / 安全密钥')
    return
  }
  state.savingMfa = true
  try {
    const res = await authApi.webauthnRegisterOptions()
    const options = res.data as any
    const publicKey = {
      ...options,
      challenge: base64UrlToBuffer(options.challenge),
      user: {
        ...options.user,
        id: base64UrlToBuffer(options.user.id),
      },
      excludeCredentials: (options.excludeCredentials || []).map((item: any) => ({
        ...item,
        id: base64UrlToBuffer(item.id),
      })),
    }
    const cred = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential | null
    if (!cred) {
      throw new Error('cancelled')
    }
    const attestation = cred.response as AuthenticatorAttestationResponse
    const payload = {
      id: cred.id,
      rawId: bufferToBase64Url(cred.rawId),
      type: cred.type,
      response: {
        clientDataJSON: bufferToBase64Url(attestation.clientDataJSON),
        attestationObject: bufferToBase64Url(attestation.attestationObject),
      },
    }
    await authApi.webauthnRegisterVerify(payload)
    await loadMfaStatus()
    window.$message.success('安全密钥已绑定')
  } catch {
    window.$message.error('安全密钥绑定失败')
  } finally {
    state.savingMfa = false
  }
}

async function loadMe() {
  const data = await authStore.refreshUserInfo()
  state.me = data
  syncForms(data)
}

function syncForms(data: any) {
  const currentProfile = data?.profile ?? {}
  state.profileForm.name = data?.name ?? currentProfile.name ?? ''
  state.profileForm.nickname = data?.nickname ?? currentProfile.nickname ?? ''
  state.profileForm.avatar = data?.avatar ?? currentProfile.avatar ?? ''
  state.profileForm.signature = currentProfile.signature ?? ''
  state.profileForm.remark = currentProfile.remark ?? ''
  state.phoneForm.phone = currentProfile.phone ?? ''
  state.emailForm.email = currentProfile.email ?? ''
  state.phoneForm.phone_login_enabled = Boolean(currentProfile.phone_login_enabled)
  state.emailForm.email_login_enabled = Boolean(currentProfile.email_login_enabled)
}

async function saveProfile() {
  state.savingProfile = true
  try {
    await authApi.updateUserCenterProfile({
      name: state.profileForm.name || null,
      nickname: state.profileForm.nickname || null,
      signature: state.profileForm.signature || null,
      remark: state.profileForm.remark || null,
    })
    await refreshMe()
    window.$message.success('保存成功')
  } finally {
    state.savingProfile = false
  }
}

async function savePassword() {
  if (state.passwordForm.new_password !== state.passwordForm.confirm_password) {
    window.$message.warning('两次输入的新密码不一致')
    return
  }
  state.savingPassword = true
  try {
    const encrypted = await encryptPasswords({
      old_password: state.passwordForm.old_password,
      new_password: state.passwordForm.new_password,
    })
    await authApi.updateUserCenterPassword({
      old_password: encrypted.values.old_password,
      new_password: encrypted.values.new_password,
      password_key_id: encrypted.password_key_id,
    })
    state.passwordForm.old_password = ''
    state.passwordForm.new_password = ''
    state.passwordForm.confirm_password = ''
    window.$message.success('密码已更新')
  } finally {
    state.savingPassword = false
  }
}

function savePhone() {
  openBindConfirm('phone')
}

async function saveEmail() {
  try {
    await emailFormRef.value?.validate()
  } catch {
    return
  }
  openBindConfirm('email')
}

function validateEmailForm(_rule: FormItemRule, value: string) {
  const text = String(value ?? '').trim()
  if (!text) {
    return state.emailForm.email_login_enabled ? new Error('请输入邮箱') : true
  }
  if (!isValidEmail(text)) {
    return new Error('请输入有效邮箱')
  }
  return true
}

function openBindConfirm(type: 'phone' | 'email') {
  state.bindConfirm.type = type
  state.bindConfirm.password = ''
  state.bindConfirm.show = true
}

async function confirmBind() {
  if (!state.bindConfirm.password) {
    window.$message.warning('请输入当前密码')
    return
  }
  const isPhone = state.bindConfirm.type === 'phone'
  state.bindConfirm.loading = true
  state.savingPhone = isPhone
  state.savingEmail = !isPhone
  try {
    const encrypted = await encryptPasswords({ password: state.bindConfirm.password })
    if (isPhone) {
      await authApi.updateUserCenterPhone({
        password: encrypted.values.password,
        password_key_id: encrypted.password_key_id,
        phone: state.phoneForm.phone || null,
        phone_login_enabled: state.phoneForm.phone_login_enabled,
      })
    } else {
      await authApi.updateUserCenterEmail({
        password: encrypted.values.password,
        password_key_id: encrypted.password_key_id,
        email: state.emailForm.email.trim() || null,
        email_login_enabled: state.emailForm.email_login_enabled,
      })
    }
    state.bindConfirm.show = false
    state.bindConfirm.password = ''
    await refreshMe()
    window.$message.success('绑定已更新')
  } finally {
    state.bindConfirm.loading = false
    state.savingPhone = false
    state.savingEmail = false
  }
}

async function refreshMe() {
  const data = await authStore.refreshUserInfo()
  state.me = data
  syncForms(data)
}

function mapNames(items?: Array<{ id: string; name: string }>) {
  return (items ?? [])
    .map((item) => item.name)
    .filter(Boolean)
    .join(' / ')
}

function displayValue(value: unknown) {
  return value ? String(value) : '未设置'
}
</script>

<template>
  <div class="w-full min-w-0">
    <NSpin :show="state.loading">
      <NGrid
        class="w-full min-w-0"
        responsive="screen"
        item-responsive
        cols="1 m:24"
        :x-gap="16"
        :y-gap="16"
      >
        <NGridItem span="1 m:7" class="min-w-0">
          <NCard
            :bordered="false"
            class="user-center-profile h-full w-full min-w-0"
            content-class="min-w-0"
            size="small"
          >
            <div class="flex flex-col items-center text-center">
              <button
                class="avatar-trigger"
                type="button"
                :title="'更换头像'"
                @click="state.avatarModalShow = true"
              >
                <NAvatar
                  v-if="avatarUrl"
                  round
                  :size="104"
                  :src="avatarUrl"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="104">
                  <NovaIcon icon="icon-park-outline:user" :size="44" />
                </NAvatar>
              </button>
              <div class="mt-4 max-w-full truncate text-xl font-medium">
                {{ displayName }}
              </div>
              <div class="mt-1 max-w-full truncate text-sm text-[var(--text-color-3)]">
                {{ state.me?.account }}
              </div>
            </div>

            <NDivider />

            <NDescriptions :column="1" label-placement="left" size="small">
              <NDescriptionsItem :label="'部门'">
                {{ mainDept }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'角色'">
                {{ mainRole }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="'联系方式'">
                {{ contactText }}
              </NDescriptionsItem>
            </NDescriptions>

            <NDivider />

            <div class="text-sm font-medium">个性签名</div>
            <div
              class="mt-2 min-h-18 rounded border border-[var(--border-color)] p-3 text-sm text-[var(--text-color-3)]"
            >
              {{ displayValue(profile.signature) }}
            </div>
          </NCard>
        </NGridItem>

        <NGridItem span="1 m:17" class="min-w-0">
          <NCard
            :bordered="false"
            class="w-full min-w-0"
            content-class="min-h-140 min-w-0"
            size="small"
          >
            <NTabs
              v-model:value="state.activeTab"
              type="line"
              animated
              class="user-center-tabs w-full min-w-0"
            >
              <NTabPane name="basic_info" :tab="'基本信息'">
                <NForm class="user-center-form w-full min-w-0" label-placement="top">
                  <NFormItem :label="'账号'">
                    <NInput :value="state.me?.account" disabled />
                  </NFormItem>
                  <NFormItem :label="'姓名'">
                    <NInput v-model:value="state.profileForm.name" />
                  </NFormItem>
                  <NFormItem :label="'昵称'">
                    <NInput v-model:value="state.profileForm.nickname" />
                  </NFormItem>
                  <NFormItem :label="'个性签名'">
                    <NInput v-model:value="state.profileForm.signature" type="textarea" />
                  </NFormItem>
                  <NFormItem :label="'备注'">
                    <NInput v-model:value="state.profileForm.remark" type="textarea" />
                  </NFormItem>
                  <NFormItem :show-label="false">
                    <NButton type="primary" :loading="state.savingProfile" @click="saveProfile">
                      保存
                    </NButton>
                  </NFormItem>
                </NForm>
              </NTabPane>

              <NTabPane name="password" :tab="'密码'">
                <NForm class="user-center-form w-full min-w-0" label-placement="top">
                  <NFormItem :label="'旧密码'">
                    <NInput
                      v-model:value="state.passwordForm.old_password"
                      type="password"
                      show-password-on="click"
                    />
                  </NFormItem>
                  <NFormItem :label="'新密码'">
                    <NInput
                      v-model:value="state.passwordForm.new_password"
                      type="password"
                      show-password-on="click"
                    />
                  </NFormItem>
                  <NFormItem :label="'确认密码'">
                    <NInput
                      v-model:value="state.passwordForm.confirm_password"
                      type="password"
                      show-password-on="click"
                    />
                  </NFormItem>
                  <NFormItem :show-label="false">
                    <NButton type="primary" :loading="state.savingPassword" @click="savePassword">
                      修改密码
                    </NButton>
                  </NFormItem>
                </NForm>
              </NTabPane>

              <NTabPane name="mfa" :tab="'双因素认证'">
                <NForm class="user-center-form w-full min-w-0" label-placement="top">
                  <NFormItem :label="'状态'">
                    <span>{{ state.mfa.enabled ? '已启用' : '未启用' }}{{ state.mfa.required ? '（组织强制）' : '' }} · Passkey {{ state.mfa.webauthnCount }}</span>
                  </NFormItem>
                  <NFormItem :show-label="false">
                    <NButton :loading="state.savingMfa" @click="registerWebAuthn">
                      绑定安全密钥 / Passkey
                    </NButton>
                  </NFormItem>
                  <template v-if="!state.mfa.totpEnabled">
                    <NFormItem :show-label="false">
                      <NButton type="primary" :loading="state.savingMfa" @click="startMfaSetup">
                        开始开通 TOTP
                      </NButton>
                    </NFormItem>
                    <NFormItem v-if="state.mfa.setupSecret" :label="'密钥'">
                      <NInput :value="state.mfa.setupSecret" readonly />
                    </NFormItem>
                    <NFormItem v-if="state.mfa.setupUri" :label="'otpauth URI'">
                      <NInput :value="state.mfa.setupUri" type="textarea" readonly />
                    </NFormItem>
                    <NFormItem v-if="state.mfa.setupSecret" :label="'动态码确认'">
                      <NInput v-model:value="state.mfa.confirmCode" placeholder="认证器 6 位码" />
                    </NFormItem>
                    <NFormItem v-if="state.mfa.setupSecret" :show-label="false">
                      <NButton type="primary" :loading="state.savingMfa" @click="confirmMfaSetup">
                        确认启用
                      </NButton>
                    </NFormItem>
                  </template>
                  <template v-if="state.mfa.enabled">
                    <NFormItem :label="'当前密码'">
                      <NInput
                        v-model:value="state.mfa.disablePassword"
                        type="password"
                        show-password-on="click"
                      />
                    </NFormItem>
                    <NFormItem v-if="state.mfa.totpEnabled" :label="'动态码 / 备份码'">
                      <NInput v-model:value="state.mfa.disableCode" />
                    </NFormItem>
                    <NFormItem v-else :show-label="false">
                      <NText depth="3">仅 Passkey 时关闭 MFA 只需验证当前密码。</NText>
                    </NFormItem>
                    <NFormItem :show-label="false">
                      <NButton type="error" :loading="state.savingMfa" @click="disableMfa">
                        关闭 MFA / Passkey
                      </NButton>
                    </NFormItem>
                  </template>
                  <NFormItem v-if="state.mfa.backupCodes.length" :label="'备份码（仅显示一次）'">
                    <NInput :value="state.mfa.backupCodes.join('\n')" type="textarea" readonly :rows="8" />
                  </NFormItem>
                </NForm>
              </NTabPane>

              <NTabPane name="phone" :tab="'手机号'">
                <NForm class="user-center-form w-full min-w-0" label-placement="top">
                  <NFormItem :label="'手机号'">
                    <NInput v-model:value="state.phoneForm.phone" />
                  </NFormItem>
                  <NFormItem :label="'启用手机号登录'">
                    <NSwitch v-model:value="state.phoneForm.phone_login_enabled" />
                  </NFormItem>
                  <NFormItem :show-label="false">
                    <NButton type="primary" :loading="state.savingPhone" @click="savePhone">
                      修改手机号
                    </NButton>
                  </NFormItem>
                </NForm>
              </NTabPane>

              <NTabPane name="email" :tab="'邮箱'">
                <NForm
                  ref="emailFormRef"
                  class="user-center-form w-full min-w-0"
                  :model="state.emailForm"
                  :rules="emailRules"
                  label-placement="top"
                >
                  <NFormItem :label="'邮箱'" path="email">
                    <NInput v-model:value="state.emailForm.email" />
                  </NFormItem>
                  <NFormItem :label="'启用邮箱登录'">
                    <NSwitch v-model:value="state.emailForm.email_login_enabled" />
                  </NFormItem>
                  <NFormItem :show-label="false">
                    <NButton type="primary" :loading="state.savingEmail" @click="saveEmail">
                      修改邮箱
                    </NButton>
                  </NFormItem>
                </NForm>
              </NTabPane>
            </NTabs>
          </NCard>
        </NGridItem>
      </NGrid>
    </NSpin>

    <NModal
      v-model:show="state.bindConfirm.show"
      preset="card"
      :title="bindConfirmTitle"
      class="max-w-120"
      :bordered="false"
      :mask-closable="false"
    >
      <NForm label-placement="top">
        <NFormItem :label="'当前密码'">
          <NInput
            v-model:value="state.bindConfirm.password"
            type="password"
            show-password-on="click"
            :placeholder="'请输入当前密码'"
            @keydown.enter="confirmBind"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="state.bindConfirm.show = false"> 取消 </NButton>
          <NButton type="primary" :loading="state.bindConfirm.loading" @click="confirmBind">
            确认
          </NButton>
        </NSpace>
      </template>
    </NModal>

    <AvatarUploadModal
      v-model:show="state.avatarModalShow"
      :avatar="avatarUrl"
      @uploaded="refreshMe"
    />
  </div>
</template>

<style scoped>
.user-center-tabs {
  min-width: 0;
}

.user-center-tabs :deep(.n-tabs-nav-scroll-content) {
  -webkit-overflow-scrolling: touch;
  touch-action: pan-x;
}

.user-center-form {
  min-width: 0;
}

.user-center-form :deep(.n-form-item) {
  min-width: 0;
}

.user-center-form :deep(.n-input) {
  width: 100%;
  min-width: min(180px, 100%);
}

.avatar-trigger {
  border: 0;
  border-radius: 999px;
  background: transparent;
  padding: 0;
  cursor: pointer;
  line-height: 0;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.avatar-trigger:hover,
.avatar-trigger:focus-visible {
  background: var(--hover-color);
  box-shadow:
    0 0 0 3px var(--card-color),
    0 0 0 5px var(--primary-color-hover);
  transform: translateY(-1px);
  outline: none;
}

.user-center-profile :deep(.n-descriptions-table) {
  width: 100%;
  table-layout: fixed;
}

.user-center-profile :deep(.n-descriptions-table-content) {
  overflow-wrap: anywhere;
}
</style>
