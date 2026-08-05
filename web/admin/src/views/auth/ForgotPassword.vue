<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import { authApi } from '@/api'
import CaptchaInput from '@/components/common/CaptchaInput.vue'
import { isValidEmail } from '@/utils'
import { encryptPasswords } from '@/utils/security'
import { computed, reactive, ref } from 'vue'
import AuthLayout from './AuthLayout.vue'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInst | null>(null)
const captchaRef = ref<InstanceType<typeof CaptchaInput> | null>(null)
const loading = ref(false)

const form = reactive({
  email: '',
  token: typeof route.query.token === 'string' ? route.query.token : '',
  password: '',
  confirmPassword: '',
  captcha_id: '',
  captcha_value: '',
})

const isResetMode = computed(() => Boolean(form.token))

function validateConfirmPassword(_rule: FormItemRule, value: string) {
  if (!value) {
    return new Error('请确认密码')
  }
  if (value !== form.password) {
    return new Error('两次输入的密码不一致')
  }
  return true
}

function validateRequiredEmail(_rule: FormItemRule, value: string) {
  const text = String(value ?? '').trim()
  if (!text) {
    return new Error('请输入登录邮箱')
  }
  if (!isValidEmail(text)) {
    return new Error('请输入有效邮箱')
  }
  return true
}

const rules = computed<FormRules>(() => ({
  email: [
    {
      validator: validateRequiredEmail,
      trigger: ['input', 'blur'],
    },
  ],
  password: [
    {
      required: isResetMode.value,
      message: '请输入新密码',
      trigger: ['input', 'blur'],
    },
    {
      min: 8,
      message: '密码至少 8 个字符',
      trigger: ['input', 'blur'],
    },
  ],
  confirmPassword: [
    {
      required: isResetMode.value,
      validator: isResetMode.value ? validateConfirmPassword : undefined,
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

async function sendLink() {
  if (isResetMode.value) {
    const emailValidation = validateRequiredEmail({} as FormItemRule, form.email)
    if (emailValidation instanceof Error) {
      window.$message.warning(emailValidation.message)
      return
    }
    if (!form.captcha_value.trim()) {
      window.$message.warning('请输入验证码')
      return
    }
  }
  else {
    try {
      await formRef.value?.validate()
    }
    catch {
      return
    }
  }
  loading.value = true
  try {
    await authApi.forgotPassword({
      email: form.email.trim(),
      captcha_id: form.captcha_id,
      captcha_value: form.captcha_value,
    })
    window.$message.success('密码重置链接已发送')
    await captchaRef.value?.refresh()
  }
  catch {
    await captchaRef.value?.refresh()
  }
  finally {
    loading.value = false
  }
}

async function resetPassword() {
  try {
    await formRef.value?.validate()
  }
  catch {
    return
  }
  loading.value = true
  try {
    const encrypted = await encryptPasswords({ password: form.password })
    await authApi.resetPassword({
      email: form.email.trim(),
      token: form.token,
      password: encrypted.values.password,
      password_key_id: encrypted.password_key_id,
      captcha_id: form.captcha_id,
      captcha_value: form.captcha_value,
    })
    window.$message.success('密码已重置，请重新登录')
    router.push('/auth/login')
  }
  catch {
    await captchaRef.value?.refresh()
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout
    variant="center"
    :title="isResetMode ? '重置密码' : '找回密码'"
    :description="
      isResetMode
        ? '请设置新密码。重置链接在过期前仅可使用一次。'
        : '请输入已启用管理端登录的邮箱，系统将发送密码重置链接。'
    "
  >
    <n-form ref="formRef" :model="form" :rules="rules" size="large" :show-label="false">
      <n-form-item path="email">
        <n-input v-model:value="form.email" clearable placeholder="登录邮箱" />
      </n-form-item>

      <template v-if="isResetMode">
        <n-form-item path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="新密码（至少 8 位）"
          />
        </n-form-item>
        <PasswordStrengthBar :password="form.password" />
        <n-form-item path="confirmPassword">
          <n-input
            v-model:value="form.confirmPassword"
            type="password"
            show-password-on="click"
            placeholder="确认新密码"
          />
        </n-form-item>
      </template>

      <n-form-item path="captcha_value">
        <CaptchaInput
          ref="captchaRef"
          v-model:captcha-id="form.captcha_id"
          v-model:captcha-value="form.captcha_value"
        />
      </n-form-item>

      <n-button
        type="primary"
        size="large"
        block
        :loading="loading"
        @click="isResetMode ? resetPassword() : sendLink()"
      >
        {{ isResetMode ? '重置密码' : '发送重置链接' }}
      </n-button>

      <div class="auth-center__links">
        <RouterLink to="/auth/login">
          返回登录
        </RouterLink>
        <n-button v-if="isResetMode" text type="primary" @click="sendLink">
          发送新链接
        </n-button>
      </div>
    </n-form>
  </AuthLayout>
</template>
