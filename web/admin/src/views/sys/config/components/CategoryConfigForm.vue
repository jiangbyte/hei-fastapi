<!-- Author: Charlie -->

<script setup lang="ts">
import AuthTokenConfigForm from './AuthTokenConfigForm.vue'
import AuthLoginConfigForm from './AuthLoginConfigForm.vue'
import AuthRegisterConfigForm from './AuthRegisterConfigForm.vue'
import AuthPasswordConfigForm from './AuthPasswordConfigForm.vue'
import AuditAlertConfigForm from './AuditAlertConfigForm.vue'
import StorageConfigForm from './StorageConfigForm.vue'
import UploadConfigForm from './UploadConfigForm.vue'
import MailConfigForm from './MailConfigForm.vue'
import MailTemplateConfigForm from './MailTemplateConfigForm.vue'

defineProps<{ category: string }>()
defineEmits<{ saved: [] }>()
</script>

<template>
  <AuthTokenConfigForm v-if="category === 'AUTH_TOKEN'" :category @saved="$emit('saved')" />
  <AuthLoginConfigForm v-else-if="category === 'AUTH_LOGIN'" :category @saved="$emit('saved')" />
  <AuthRegisterConfigForm
    v-else-if="category === 'AUTH_REGISTER'"
    :category
    @saved="$emit('saved')"
  />
  <AuthPasswordConfigForm
    v-else-if="category === 'AUTH_PASSWORD'"
    :category
    @saved="$emit('saved')"
  />
  <AuditAlertConfigForm v-else-if="category === 'AUDIT_ALERT'" :category @saved="$emit('saved')" />
  <StorageConfigForm v-else-if="category === 'STORAGE'" @saved="$emit('saved')" />
  <UploadConfigForm v-else-if="category === 'UPLOAD'" :category @saved="$emit('saved')" />
  <MailConfigForm v-else-if="category === 'MAIL'" :category @saved="$emit('saved')" />
  <MailTemplateConfigForm v-else-if="category === 'MAIL_TEMPLATE'" @saved="$emit('saved')" />
</template>
