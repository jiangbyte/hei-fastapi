<!-- Author: Charlie -->

<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import { computed, reactive, ref } from 'vue'
import CaptchaInput from '@/components/common/CaptchaInput.vue'
import { useAuthStore } from '@/stores'
import { isValidEmail } from '@/utils'
import { encryptPasswords } from '@/utils/security'
import AuthLayout from './AuthLayout.vue'

type LoginType = 'ACCOUNT' | 'EMAIL' | 'PHONE'

const route = useRoute()
const authStore = useAuthStore()
const formRef = ref<FormInst | null>(null)
const captchaRef = ref<InstanceType<typeof CaptchaInput> | null>(null)
const loading = ref(false)
const activeType = ref<LoginType>('ACCOUNT')
const mfaChallengeId = ref('')
const mfaCode = ref('')
const webauthnOptions = ref<Record<string, unknown> | null>(null)

const loginTypes: Array<{ key: LoginType; label: string; placeholder: string }> = [
  { key: 'ACCOUNT', label: '账号', placeholder: '请输入管理员账号' },
  { key: 'EMAIL', label: '邮箱', placeholder: '请输入登录邮箱' },
  { key: 'PHONE', label: '手机号', placeholder: '请输入登录手机号' },
]

const form = reactive({
  account: '',
  email: '',
  phone: '',
  password: '',
  captcha_id: '',
  captcha_value: '',
  remember: true,
})

const currentLogin = computed(() => loginTypes.find(item => item.key === activeType.value)!)
const activeField = computed(() => activeType.value.toLowerCase() as 'account' | 'email' | 'phone')
const mfaStep = computed(() => Boolean(mfaChallengeId.value))

function validateLoginIdentity(_rule: FormItemRule, value: string) {
  const text = String(value ?? '').trim()
  if (!text) {
    return new Error(`请输入${currentLogin.value.label}`)
  }
  if (activeType.value === 'EMAIL' && !isValidEmail(text)) {
    return new Error('请输入有效邮箱')
  }
  return true
}

const rules = computed<FormRules>(() => ({
  [activeField.value]: [
    {
      validator: validateLoginIdentity,
      trigger: ['input', 'blur'],
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur'],
    },
  ],
  captcha_value: [
    {
      required: true,
      message: '请输入验证码',
      trigger: ['input', 'blur'],
    },
  ],
}))

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  }
  catch {
    return
  }

  loading.value = true
  try {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    const encrypted = await encryptPasswords({ password: form.password })
    const result = await authStore.login(
      form[activeField.value].trim(),
      encrypted.values.password || '',
      redirect,
      form.remember,
      activeType.value,
      {
        password_key_id: encrypted.password_key_id,
        captcha_id: form.captcha_id,
        captcha_value: form.captcha_value,
      },
    )
    if (result.mfaRequired) {
      mfaChallengeId.value = result.challengeId
      webauthnOptions.value = result.webauthnOptions ?? null
      window.$message.info('请输入动态验证码、备份码，或使用安全密钥')
      return
    }
    window.$message.success('登录成功')
  }
  catch {
    await captchaRef.value?.refresh()
  }
  finally {
    loading.value = false
  }
}

async function handleMfaSubmit() {
  if (!mfaCode.value.trim()) {
    window.$message.warning('请输入验证码')
    return
  }
  loading.value = true
  try {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    await authStore.completeMfaLogin(mfaChallengeId.value, mfaCode.value.trim(), redirect)
    window.$message.success('登录成功')
  }
  catch {
    // 保留 MFA 步骤
  }
  finally {
    loading.value = false
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

async function handleWebAuthnLogin() {
  if (!webauthnOptions.value || !window.PublicKeyCredential) {
    window.$message.warning('当前环境不支持安全密钥')
    return
  }
  loading.value = true
  try {
    const options = webauthnOptions.value as any
    const publicKey = {
      ...options,
      challenge: base64UrlToBuffer(options.challenge),
      allowCredentials: (options.allowCredentials || []).map((item: any) => ({
        ...item,
        id: base64UrlToBuffer(item.id),
      })),
    }
    const cred = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential | null
    if (!cred) {
      throw new Error('cancelled')
    }
    const response = cred.response as AuthenticatorAssertionResponse
    const payload = {
      id: cred.id,
      rawId: bufferToBase64Url(cred.rawId),
      type: cred.type,
      response: {
        clientDataJSON: bufferToBase64Url(response.clientDataJSON),
        authenticatorData: bufferToBase64Url(response.authenticatorData),
        signature: bufferToBase64Url(response.signature),
        userHandle: response.userHandle ? bufferToBase64Url(response.userHandle) : null,
      },
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    await authStore.completeMfaLogin(mfaChallengeId.value, '', redirect, payload)
    window.$message.success('登录成功')
  }
  catch {
    window.$message.error('安全密钥验证失败')
  }
  finally {
    loading.value = false
  }
}

function backToPassword() {
  mfaChallengeId.value = ''
  mfaCode.value = ''
  webauthnOptions.value = null
}
</script>

<template>
  <AuthLayout title="管理端登录" subtitle="欢迎回来">
    <n-form
      v-if="!mfaStep"
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      @submit.prevent="handleSubmit"
    >
      <n-tabs v-model:value="activeType" type="segment" class="auth-login-tabs">
        <n-tab-pane v-for="item in loginTypes" :key="item.key" :name="item.key" :tab="item.label" />
      </n-tabs>

      <n-form-item :path="activeField">
        <n-input
          v-model:value="form[activeField]"
          :placeholder="currentLogin.placeholder"
          clearable
        />
      </n-form-item>
      <n-form-item path="password">
        <n-input
          v-model:value="form.password"
          type="password"
          show-password-on="click"
          placeholder="请输入密码"
        />
      </n-form-item>
      <n-form-item path="captcha_value">
        <CaptchaInput
          ref="captchaRef"
          v-model:captcha-id="form.captcha_id"
          v-model:captcha-value="form.captcha_value"
        />
      </n-form-item>
      <div class="auth-form-row">
        <n-checkbox v-model:checked="form.remember">
          记住我
        </n-checkbox>
        <RouterLink to="/auth/forgot-password">
          忘记密码？
        </RouterLink>
      </div>
      <n-button
        class="auth-submit"
        type="primary"
        block
        attr-type="submit"
        :loading="loading"
      >
        登录
      </n-button>
    </n-form>

    <div v-else class="mfa-step">
      <p class="mfa-hint">
        已启用双因素认证，请输入应用中的 6 位动态码或备份码。
      </p>
      <n-input
        v-model:value="mfaCode"
        size="large"
        placeholder="动态验证码 / 备份码"
        @keyup.enter="handleMfaSubmit"
      />
      <n-button
        class="auth-submit"
        type="primary"
        block
        :loading="loading"
        @click="handleMfaSubmit"
      >
        验证并登录
      </n-button>
      <n-button
        v-if="webauthnOptions"
        block
        :loading="loading"
        @click="handleWebAuthnLogin"
      >
        使用安全密钥 / Passkey
      </n-button>
      <n-button quaternary block class="mfa-back" @click="backToPassword">
        返回账号密码
      </n-button>
    </div>
  </AuthLayout>
</template>

<style scoped>
.auth-login-tabs {
  margin-bottom: 4px;
}

.auth-login-tabs :deep(.n-tabs-pane-wrapper) {
  overflow: visible;
}

.auth-login-tabs :deep(.n-tabs-nav) {
  margin-bottom: 16px;
}

.auth-form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: -2px 0 22px;
  font-size: 14px;
}

.auth-form-row a {
  color: var(--n-primary-color, #18a058);
  text-decoration: none;
}

.auth-submit {
  margin-top: 2px;
}

.mfa-step {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mfa-hint {
  margin: 0;
  color: var(--n-text-color-3, #666);
  font-size: 14px;
  line-height: 1.5;
}

.mfa-back {
  margin-top: 4px;
}

@media (max-width: 420px) {
  .auth-form-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
