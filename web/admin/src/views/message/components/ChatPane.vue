<script setup lang="ts">
import { computed, inject, nextTick, onUnmounted, reactive, ref, watch } from 'vue'
import { useThemeVars } from 'naive-ui'
import { formatDateTime, isImageFile, resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { fileApi, messageApi } from '@/api'
import type { Message, Conversation } from '../types'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const props = defineProps<{
  conversation: Conversation
  draft?: { text: string; attachments: any[] }
}>()
const emit = defineEmits<{
  close: []
  'update:draft': [draft: { text: string; attachments: any[] }]
}>()

const themeVars = useThemeVars()
const data = inject(MESSAGE_DATA_KEY)!
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const composerText = ref(props.draft?.text ?? '')
const selectedAttachments = ref<any[]>(props.draft?.attachments ?? [])
const selectedFiles = ref<File[]>([])
watch(
  () => props.draft,
  (d) => {
    if (d) {
      composerText.value = d.text
      selectedAttachments.value = d.attachments
      selectedFiles.value = []
    }
  },
  { immediate: false },
)
watch(
  [composerText, selectedAttachments],
  () => {
    emit('update:draft', { text: composerText.value, attachments: selectedAttachments.value })
  },
  { deep: true },
)
const fileInputRef = ref<HTMLInputElement | null>(null)
const messageListRef = ref<HTMLElement | null>(null)

const messageState = reactive({
  visibleStart: 0,
  visibleMessages: [] as Message[],
  loadingOlder: false,
  loading: false,
  hasMoreOlder: true,
})

const visibleMessages = computed(() => messageState.visibleMessages)
const hasMoreOlder = computed(() => messageState.hasMoreOlder)

const conversationMessages = computed(
  () => data.messagesByConversation[props.conversation.id] ?? [],
)

let alive = true
onUnmounted(() => {
  alive = false
  if (syncTimer) {
    clearTimeout(syncTimer)
    syncTimer = null
  }
})

let syncTimer: ReturnType<typeof setTimeout> | null = null
function scheduleSync(scrollBottom = false) {
  if (!alive) return
  if (syncTimer) clearTimeout(syncTimer)
  syncTimer = setTimeout(() => {
    if (!alive) return
    syncVisibleMessages()
    if (scrollBottom) void nextTick(() => scrollMessagesToBottom())
  }, 50)
}

function syncVisibleMessages() {
  if (!props.conversation) return
  const history = conversationMessages.value
  // 已加载更早历史时保持从头部展示；否则只保留最近窗口
  if (messageState.visibleStart === 0 && messageState.visibleMessages.length > 20) {
    messageState.visibleMessages = history.slice()
  } else {
    messageState.visibleStart = Math.max(0, history.length - 20)
    messageState.visibleMessages = history.slice(messageState.visibleStart)
  }
}

async function loadOlderMessages() {
  if (messageState.loadingOlder) return
  messageState.loadingOlder = true
  try {
    // 后端返回倒序（最新在前），前端目前有 totalCount 条，需要第 totalCount/20+1 页
    const totalCount = conversationMessages.value.length
    const page = Math.floor(totalCount / 20) + 1
    const res = await messageApi.messagePage({
      conversation_id: props.conversation.id,
      current: page,
      size: 20,
    })
    const records = res?.data?.records ?? []
    if (records.length) {
      // 后端返回的也是倒序，反转成正序后再拼接到数组头部
      records.reverse()
      const existing = new Set(conversationMessages.value.map((m) => m.id))
      const newOnes = records.filter((m: Message) => !existing.has(m.id))
      if (newOnes.length) {
        conversationMessages.value.unshift(...newOnes)
      }
      // 显示所有已加载消息（可见窗口包含更早消息）
      messageState.visibleStart = 0
      messageState.visibleMessages = conversationMessages.value
    }
    // 如果这次返回的记录数 < 20，说明没有更多历史消息了
    if (records.length < 20) {
      messageState.hasMoreOlder = false
    }
  } catch {
    /* silent */
  } finally {
    messageState.loadingOlder = false
  }
}

async function loadMessages() {
  messageState.loading = true
  messageState.hasMoreOlder = true
  try {
    const res = await messageApi.messagePage({
      conversation_id: props.conversation.id,
      current: 1,
      size: 20,
    })
    const records = (res?.data?.records ?? []).reverse() // 后端倒序，反转成正序
    // 合并已有（可能从 WS 收到）和新加载的消息
    const merged = [...records]
    const existingIds = new Set(records.map((m: Message) => m.id))
    const existing = data.messagesByConversation[props.conversation.id] ?? []
    for (const m of existing) {
      if (!existingIds.has(m.id)) merged.push(m)
    }
    merged.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    data.messagesByConversation[props.conversation.id] = merged
    // 根据总消息数判断是否有更早的历史消息
    const total = (res?.data as any)?.total ?? merged.length
    messageState.hasMoreOlder = total > merged.length
    syncVisibleMessages()
    await nextTick()
    scrollMessagesToBottom()
  } catch {
    // 请求失败时保留已有数据
  } finally {
    messageState.loading = false
  }
}

function handleMessageScroll(event: Event) {
  const target = event.currentTarget as HTMLElement
  if (target.scrollTop <= 24) void loadOlderMessages()
}

function isOwnMessage(message: Message): boolean {
  return (
    message.sender_account_id === data.profile?.account_id &&
    message.sender_account_type === data.profile?.account_type
  )
}

function scrollMessagesToBottom() {
  const target = messageListRef.value
  if (target) target.scrollTop = target.scrollHeight
}

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

function messageBubbleStyle(isMine: boolean) {
  const v = themeVars.value
  return isMine
    ? { backgroundColor: v.primaryColor, border: `1px solid ${v.primaryColor}`, color: '#ffffff' }
    : { backgroundColor: v.cardColor, border: `1px solid ${v.borderColor}`, color: v.textColor1 }
}

async function sendMessage() {
  const content = composerText.value.trim()
  if (!content && !selectedAttachments.value.length) return

  // ── Upload pending files ──
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

  const convId = props.conversation.id
  try {
    const res = await messageApi.sendMessage({
      conversation_id: convId,
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
      const history = conversationMessages.value
      if (!history.some((m) => m.id === res.data.id)) {
        data.messagesByConversation[convId] = [...history, res.data]
      }
      const conv = data.conversations.find((c) => c.id === convId)
      if (conv) {
        conv.last_message_id = res.data.id
        conv.last_message_at = res.data.created_at
      }
      scheduleSync(true)
    }
  } catch {
    window.$message?.error?.('发送失败')
  }

  composerText.value = ''
  selectedAttachments.value = []
  void nextTick(() => scrollMessagesToBottom())
}

watch(
  () => props.conversation?.id,
  (newId) => {
    if (newId) loadMessages()
  },
  { immediate: true },
)

// 同引用 push 不会触发浅 watch；监听 length + 尾部 id。仅尾部变化时滚到底
watch(
  () => {
    const id = props.conversation?.id ?? ''
    const list = data.messagesByConversation[id] ?? []
    const last = list.length ? list[list.length - 1] : null
    return { convId: id, len: list.length, lastId: last?.id ?? '' }
  },
  (cur, prev) => {
    if (!cur.convId) return
    const sameConv = Boolean(prev && prev.convId === cur.convId)
    const newTail = sameConv && Boolean(cur.lastId) && cur.lastId !== prev!.lastId
    scheduleSync(newTail)
  },
)
</script>

<template>
  <div v-if="conversation" class="flex h-full min-h-0 flex-col">
    <div
      class="flex items-center justify-between gap-3 border-b px-4 py-3"
      :style="{ borderColor: themeVars.borderColor }"
    >
      <div class="flex min-w-0 items-center gap-3 overflow-hidden">
        <NButton v-if="ui.isMobile.value" text size="small" @click="actions.backToListPane()">
          <template #icon>
            <NovaIcon icon="icon-park-outline:arrow-left" :size="18" />
          </template>
        </NButton>
        <NAvatar
          v-if="conversation.avatar"
          round
          :size="42"
          class="shrink-0"
          :src="resolveFileUrl(conversation.avatar)"
          :img-props="avatarImgProps"
        />
        <NAvatar v-else round :size="42" class="shrink-0">
          {{ (conversation.title || '?').charAt(0) }}
        </NAvatar>
        <NThing
          :title="conversation.title"
          :description="conversation.conversation_type === 'GROUP' ? '群聊' : '私聊'"
        />
      </div>
      <NFlex :size="4">
        <NButton text size="small" aria-label="关闭会话" @click="emit('close')">
          <template #icon>
            <NovaIcon icon="icon-park-outline:close" :size="18" />
          </template>
        </NButton>
      </NFlex>
    </div>

    <div class="flex min-h-0 flex-1 flex-col">
      <div
        v-if="hasMoreOlder"
        class="border-b px-4 py-2 text-center"
        :style="{ borderColor: themeVars.borderColor }"
      >
        <NButton text size="small" :loading="messageState.loadingOlder" @click="loadOlderMessages">
          上滑加载更早消息
        </NButton>
      </div>
      <div
        v-if="messageState.loading && !visibleMessages.length"
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
        <NEmpty v-else-if="!messageState.loading" class="py-12" description="暂无消息" />
      </div>

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
  <NEmpty v-else class="h-full flex items-center justify-center" description="请选择会话" />
</template>
