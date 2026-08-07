<!-- Author: Charlie -->

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, isImageFile, resolveFileUrl } from '@/utils'
import { fileApi, messageApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { Message, Conversation } from '../../views/message/types'
import { useImClient } from '../../views/message/useImClient'

const emit = defineEmits<{
  changed: [payload: { type: string; id: string }]
}>()

const authStore = useAuthStore()
const themeVars = useThemeVars()
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any

const show = ref(false)
const cid = ref('')
const conversation = ref<Conversation | null>(null)
const allMessages = ref<Message[]>([])
const visibleMessages = ref<Message[]>([])
const hasMoreOlder = ref(true)
const loading = ref(false)
const loadingOlder = ref(false)
const composerText = ref('')
const selectedAttachments = ref<any[]>([])
const selectedFiles = ref<File[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const messageListRef = ref<HTMLElement | null>(null)

const modalTitle = computed(() => conversation.value?.title || '会话')
const conversationTypeLabel = computed(() =>
  conversation.value?.conversation_type === 'GROUP' ? '群聊' : '私聊',
)

const ws = useImClient({
  onNewMessage(msgData: any) {
    if (msgData.conversation_id !== cid.value) return
    if (!allMessages.value.some((m) => m.id === msgData.id)) {
      allMessages.value.push(msgData)
      syncVisibleMessages()
    }
    if (msgData.id) ws.markConversationRead(cid.value, msgData.id)
  },
  onKick() {
    window.$message?.warning?.('会话已失效，请重新登录')
    void authStore.logout('/auth/login')
  },
})

/* ---- 消息辅助 ---- */

function isOwnMessage(message: Message): boolean {
  const user = authStore.userInfo
  return (
    message.sender_account_id === user?.accountId &&
    message.sender_account_type === user?.accountType
  )
}

function messageBubbleStyle(isMine: boolean) {
  const v = themeVars.value
  return isMine
    ? { backgroundColor: v.primaryColor, border: `1px solid ${v.primaryColor}`, color: '#ffffff' }
    : { backgroundColor: v.cardColor, border: `1px solid ${v.borderColor}`, color: v.textColor1 }
}

/* ---- 同步 / 分页 ---- */

function syncVisibleMessages() {
  visibleMessages.value = allMessages.value.slice(Math.max(0, allMessages.value.length - 20))
}

function scrollMessagesToBottom() {
  const target = messageListRef.value
  if (target) target.scrollTop = target.scrollHeight
}

async function loadMessages() {
  loading.value = true
  hasMoreOlder.value = true
  try {
    const res = await messageApi.messagePage({
      conversation_id: cid.value,
      current: 1,
      size: 20,
    })
    const records = (res?.data?.records ?? []).reverse()
    allMessages.value = records
    const total = (res?.data as any)?.total ?? records.length
    hasMoreOlder.value = total > records.length
    syncVisibleMessages()
    await nextTick()
    scrollMessagesToBottom()
  } catch {
    /* 静默 */
  } finally {
    loading.value = false
  }
}

async function loadOlderMessages() {
  if (loadingOlder.value) return
  loadingOlder.value = true
  try {
    const totalCount = allMessages.value.length
    const page = Math.floor(totalCount / 20) + 1
    const res = await messageApi.messagePage({
      conversation_id: cid.value,
      current: page,
      size: 20,
    })
    const records = res?.data?.records ?? []
    if (records.length) {
      records.reverse()
      const existing = new Set(allMessages.value.map((m) => m.id))
      const newOnes = records.filter((m: Message) => !existing.has(m.id))
      if (newOnes.length) {
        allMessages.value.unshift(...newOnes)
      }
      visibleMessages.value = allMessages.value
    }
    if (records.length < 20) {
      hasMoreOlder.value = false
    }
  } catch {
    /* 静默 */
  } finally {
    loadingOlder.value = false
  }
}

function handleMessageScroll(event: Event) {
  const target = event.currentTarget as HTMLElement
  if (target.scrollTop <= 24) void loadOlderMessages()
}

/* ---- 输入区 ---- */

function handleAddFileButtonClick() {
  fileInputRef.value?.click()
}

function handleFileInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!files.length) return
  const startIndex = selectedAttachments.value.length
  files.forEach((file, i) => {
    selectedFiles.value[startIndex + i] = file
  })
  selectedAttachments.value = [
    ...selectedAttachments.value,
    ...files.map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
      url: '',
    })),
  ]
  input.value = ''
}

function removeAttachment(index: number) {
  selectedFiles.value.splice(index, 1)
  selectedAttachments.value = selectedAttachments.value.filter((_, i) => i !== index)
}

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

async function sendMessage() {
  const content = composerText.value.trim()
  if (!content && !selectedAttachments.value.length) return

  // ── 上传待发送文件 ──
  const pending = selectedAttachments.value
    .map((a, i) => ({ attachment: a, file: selectedFiles.value[i], index: i }))
    .filter(({ attachment, file }) => !attachment.url && file)
  if (pending.length) {
    for (const { attachment, file } of pending) {
      try {
        const res = await fileApi.upload(file)
        const data = res?.data as
          | { id?: string; url?: string; name?: string; content_type?: string; size?: number }
          | undefined
        if (data) {
          attachment.url = data.url || data.id || ''
          attachment.file_id = data.id
        }
      } catch {
        window.$message?.error?.(`文件 "${attachment.name}" 上传失败`)
        return
      }
    }
    selectedFiles.value = []
  }

  try {
    const res = await messageApi.sendMessage({
      conversation_id: cid.value,
      client_msg_id: crypto.randomUUID(),
      content: content || ' ',
      attachments: selectedAttachments.value.length
        ? selectedAttachments.value.map((a: any) => ({
            file_id: a.file_id,
            name: a.name,
            url: a.url,
            size: a.size,
            content_type: a.type,
          }))
        : undefined,
    })
    if (res?.data) {
      if (!allMessages.value.some((m) => m.id === res.data.id)) {
        allMessages.value.push(res.data)
        syncVisibleMessages()
      }
    }
  } catch {
    window.$message?.error?.('发送失败')
  }

  composerText.value = ''
  selectedAttachments.value = []
  await nextTick()
  scrollMessagesToBottom()
}

/* ---- 打开 / 暴露 ---- */

async function open(
  conversationId: string,
  info?: { title?: string; avatar?: string; conversationType?: string },
) {
  cid.value = conversationId
  conversation.value = null
  allMessages.value = []
  visibleMessages.value = []
  composerText.value = ''
  selectedAttachments.value = []
  selectedFiles.value = []
  hasMoreOlder.value = true
  loading.value = false

  show.value = true
  await nextTick()

  // 直接使用列表传入的会话信息，避免额外一次 API 调用
  conversation.value = {
    id: conversationId,
    title: info?.title || '会话',
    avatar: info?.avatar || null,
    conversation_type: info?.conversationType || 'DIRECT',
  } as Conversation

  messageApi.markConversationRead({ id: conversationId }).catch(() => {})
  emit('changed', { type: 'message', id: conversationId })
  ws.connect()
  await loadMessages()
}

defineExpose({ open })
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    draggable
    :mask-closable="false"
    :title="modalTitle"
    style="width: 760px"
  >
    <div class="h-[560px] flex min-h-0 flex-col -mx-16px -mb-16px">
      <!-- 头部：会话信息栏 -->
      <div
        v-if="conversation"
        class="flex items-center gap-3 border-b px-4 py-2.5"
        :style="{ borderColor: themeVars.borderColor }"
      >
        <NAvatar
          v-if="conversation.avatar"
          round
          :size="32"
          class="shrink-0"
          :src="resolveFileUrl(conversation.avatar)"
          :img-props="avatarImgProps"
        />
        <NAvatar v-else round :size="32" class="shrink-0">
          {{ (conversation.title || '会话').charAt(0) }}
        </NAvatar>
        <div class="min-w-0">
          <div class="text-sm font-600">
            {{ conversation.title }}
          </div>
          <div class="text-xs" :style="{ color: themeVars.textColor3 }">
            {{ conversationTypeLabel }}
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="flex min-h-0 flex-1 flex-col">
        <div
          v-if="hasMoreOlder"
          class="border-b px-4 py-2 text-center"
          :style="{ borderColor: themeVars.borderColor }"
        >
          <NButton text size="small" :loading="loadingOlder" @click="loadOlderMessages">
            上滑加载更早消息
          </NButton>
        </div>
        <div
          v-if="loading && !visibleMessages.length"
          class="flex items-center justify-center py-12 text-sm"
          :style="{ color: themeVars.textColor3 }"
        >
          加载中...
        </div>
        <div
          ref="messageListRef"
          class="flex min-h-0 flex-1 flex-col gap-3 overflow-auto px-4 py-4"
          @scroll.passive="handleMessageScroll"
        >
          <div v-if="visibleMessages.length" class="flex flex-col gap-3">
            <div
              v-for="message in visibleMessages"
              :key="message.id"
              class="flex items-start gap-2"
              :class="isOwnMessage(message) ? 'flex-row-reverse' : ''"
            >
              <NAvatar
                v-if="message.sender_avatar"
                round
                :size="28"
                class="shrink-0"
                :src="resolveFileUrl(message.sender_avatar)"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="28" class="shrink-0">
                {{ message.sender_nickname?.charAt(0) || message.sender_name?.charAt(0) || '?' }}
              </NAvatar>
              <div class="min-w-0 max-w-[min(68%,640px)]">
                <div
                  class="mb-1 flex gap-2 text-xs"
                  :class="isOwnMessage(message) ? 'justify-end' : 'justify-start'"
                  :style="{ color: themeVars.textColor3 }"
                >
                  <span>{{ message.sender_nickname || message.sender_name || '未知' }}</span>
                  <span>{{ formatDateTime(message.created_at) }}</span>
                </div>
                <div
                  class="rounded-2 px-3 py-2 text-sm leading-6"
                  :style="messageBubbleStyle(isOwnMessage(message))"
                >
                  <div v-if="message.is_revoked" class="italic opacity-60">消息已撤回</div>
                  <div v-else class="break-words">
                    {{ message.content }}
                  </div>
                  <div v-if="message.attachments?.length" class="mt-2 flex flex-col gap-2">
                    <template v-for="attachment in message.attachments" :key="attachment.id">
                      <div
                        v-if="isImageFile(attachment)"
                        class="group/image relative overflow-hidden rounded-1"
                      >
                        <NImage
                          :src="resolveFileUrl(attachment.url)"
                          :alt="attachment.name"
                          height="160"
                          class="max-w-full"
                          object-fit="cover"
                          :img-props="{ referrerPolicy: 'no-referrer', loading: 'lazy' }"
                        />
                        <a
                          :href="resolveFileUrl(attachment.url)"
                          download
                          :title="'下载 ' + attachment.name"
                          class="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded-1 bg-black/40 text-white opacity-0 transition-opacity group-hover/image:opacity-100"
                          @click.stop
                        >
                          <NovaIcon icon="icon-park-outline:download" :size="14" />
                        </a>
                      </div>
                      <a
                        v-else
                        :href="resolveFileUrl(attachment.url)"
                        download
                        :title="attachment.name"
                        class="flex items-center gap-3 rounded-1 border px-3 py-2"
                        :class="isOwnMessage(message) ? 'border-white/20 bg-white/10' : ''"
                        :style="
                          !isOwnMessage(message)
                            ? {
                                borderColor: themeVars.borderColor,
                                backgroundColor: themeVars.bodyColor,
                              }
                            : {}
                        "
                      >
                        <NovaIcon icon="icon-park-outline:file" :size="16" />
                        <div class="min-w-0 flex-1">
                          <div class="message-ellipsis text-xs font-600">{{ attachment.name }}</div>
                          <div class="mt-0.5 text-[10px] opacity-80">
                            {{ formatFileSize(attachment.size) }}
                          </div>
                        </div>
                      </a>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <NEmpty v-else-if="!loading" class="py-12" description="暂无消息" />
        </div>

        <!-- 输入区 -->
        <div class="border-t p-4" :style="{ borderColor: themeVars.borderColor }">
          <input
            ref="fileInputRef"
            type="file"
            multiple
            class="hidden"
            @change="handleFileInputChange"
          />
          <div v-if="selectedAttachments.length" class="mb-3 flex flex-wrap gap-2">
            <NTag
              v-for="(attachment, index) in selectedAttachments"
              :key="`${attachment.name}-${index}`"
              closable
              :bordered="false"
              @close="removeAttachment(index)"
            >
              <template #icon>
                <NovaIcon icon="icon-park-outline:file" :size="14" />
              </template>
              {{ attachment.name }}
            </NTag>
          </div>
          <NInput
            v-model:value="composerText"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="输入消息，Enter 发送，Shift + Enter 换行"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div
            class="mt-3 flex items-center justify-between gap-3 text-xs"
            :style="{ color: themeVars.textColor3 }"
          >
            <div class="flex items-center gap-2">
              <NButton
                quaternary
                size="small"
                aria-label="发送文件"
                @click="handleAddFileButtonClick"
              >
                <template #icon>
                  <NovaIcon icon="icon-park-outline:folder-upload" :size="16" />
                </template>
              </NButton>
            </div>
            <NButton
              type="primary"
              :disabled="!composerText.trim() && !selectedAttachments.length"
              @click="sendMessage"
            >
              发送
            </NButton>
          </div>
        </div>
      </div>
    </div>
  </NModal>
</template>

<style scoped>
.message-ellipsis {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
