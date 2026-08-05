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
    await authStore.login(
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
    window.$message.success('登录成功')
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
  <AuthLayout title="登录">
    <n-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      :show-label="false"
      @submit.prevent="handleSubmit"
    >
      <n-tabs v-model:value="activeType" type="line" animated class="auth-login-tabs">
        <n-tab-pane v-for="item in loginTypes" :key="item.key" :name="item.key" :tab="item.label">
          <n-form-item :path="activeField">
            <n-input
              v-model:value="form[activeField]"
              :placeholder="item.placeholder"
              clearable
            />
          </n-form-item>
        </n-tab-pane>
      </n-tabs>

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
          已有账号，忘记密码？
        </RouterLink>
      </div>

      <n-button
        class="auth-submit"
        type="primary"
        size="large"
        block
        attr-type="submit"
        :loading="loading"
      >
        登录
      </n-button>
    </n-form>
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

@media (max-width: 420px) {
  .auth-form-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
