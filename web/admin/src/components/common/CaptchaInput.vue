<!-- Author: Charlie -->

<script setup lang="ts">
import { authApi } from '@/api'
import { computed, onMounted, ref } from 'vue'

const captchaId = defineModel<string>('captchaId', { required: true })
const captchaValue = defineModel<string>('captchaValue', { required: true })
const loading = ref(false)
const imageBase64 = ref('')

const imageSrc = computed(() =>
  imageBase64.value ? `data:image/svg+xml;base64,${imageBase64.value}` : '',
)

async function refresh() {
  loading.value = true
  try {
    const response = await authApi.captcha()
    captchaId.value = response.data.captcha_id
    captchaValue.value = ''
    imageBase64.value = response.data.image_base64
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>

<template>
  <div class="captcha-input">
    <NInput v-model:value="captchaValue" :placeholder="'请输入验证码'" clearable>
      <template #prefix>
        <NovaIcon icon="icon-park-outline:check-correct" />
      </template>
    </NInput>
    <button class="captcha-image" type="button" :disabled="loading" @click="refresh">
      <NSpin :show="loading" size="small">
        <img v-if="imageSrc" :src="imageSrc" alt="验证码" />
      </NSpin>
    </button>
  </div>
</template>

<style scoped>
.captcha-input {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px;
  gap: 10px;
  align-items: center;
}

.captcha-image {
  width: 140px;
  height: 44px;
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  background: #f8fafc;
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
}

.captcha-image:disabled {
  cursor: wait;
}

.captcha-image img {
  display: block;
  width: 140px;
  height: 44px;
}
</style>
