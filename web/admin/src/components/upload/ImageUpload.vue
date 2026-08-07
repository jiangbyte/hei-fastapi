<!-- Author: Charlie -->

<script setup lang="ts">
import FileUpload from './FileUpload.vue'

defineProps<{
  value?: string | null
}>()

defineEmits<{
  'update:value': [value: string]
  uploaded: [file: any]
}>()
</script>

<template>
  <FileUpload
    :value="value"
    accept="image/jpeg,image/png,image/webp,image/gif"
    preview="image"
    @update:value="$emit('update:value', $event)"
    @uploaded="$emit('uploaded', $event)"
  />
</template>
