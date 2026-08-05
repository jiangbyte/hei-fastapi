import { defineStore } from 'pinia'
import { ref } from 'vue'

/** Admin IM 弹窗中心：全局打开/关闭，避免全屏页面打断工作流 */
export const useImCenterStore = defineStore('imCenter', () => {
  const visible = ref(false)
  const initialConversationId = ref<string | null>(null)
  const initialSection = ref<'chat' | 'contacts' | 'notice'>('chat')

  function open(options?: {
    conversationId?: string | null
    section?: 'chat' | 'contacts' | 'notice'
  }) {
    initialConversationId.value = options?.conversationId ?? null
    initialSection.value = options?.section ?? 'chat'
    visible.value = true
  }

  function close() {
    visible.value = false
    initialConversationId.value = null
  }

  return {
    visible,
    initialConversationId,
    initialSection,
    open,
    close,
  }
})
