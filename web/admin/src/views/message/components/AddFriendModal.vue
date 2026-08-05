<script setup lang="ts">
import { resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { computed, inject, ref, watch } from 'vue'
import { useThemeVars } from 'naive-ui'
import { messageApi } from '@/api'
import { MESSAGE_DATA_KEY } from '../provide-keys'

const themeVars = useThemeVars()
const data = inject(MESSAGE_DATA_KEY)!

type AddMode = 'friend' | 'group'

const props = withDefaults(defineProps<{ initialMode?: AddMode }>(), { initialMode: 'friend' })
const show = defineModel<boolean>('show', { required: true })
const addMode = ref<AddMode>(props.initialMode)
const addSearchText = ref('')
const addSearchResults = ref<any[]>([])
const addSearchLoading = ref(false)
const applyingKeys = ref<Set<string>>(new Set())

const addSearchPlaceholder = computed(() =>
  addMode.value === 'friend' ? '搜索用户' : '搜索群组名称',
)

function userKey(user: any) {
  return `${user.account_type}-${user.account_id}`
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => show.value,
  (v) => {
    if (v) addMode.value = props.initialMode
  },
)
watch([addSearchText, addMode], () => {
  if (searchTimer) clearTimeout(searchTimer)
  const keyword = addSearchText.value.trim()
  if (!keyword) {
    addSearchResults.value = []
    return
  }
  addSearchLoading.value = true
  searchTimer = setTimeout(async () => {
    try {
      if (addMode.value === 'friend') {
        const res = await messageApi.searchUsers(keyword)
        addSearchResults.value = res?.data ?? []
      } else {
        const res = await messageApi.searchGroups(keyword)
        addSearchResults.value = res?.data ?? []
      }
    } catch {
      addSearchResults.value = []
    } finally {
      addSearchLoading.value = false
    }
  }, 300)
})

function patchUser(key: string, patch: Record<string, any>) {
  addSearchResults.value = addSearchResults.value.map((u) =>
    userKey(u) === key ? { ...u, ...patch } : u,
  )
}

function patchGroup(id: string, patch: Record<string, any>) {
  addSearchResults.value = addSearchResults.value.map((g) =>
    g.id === id ? { ...g, ...patch } : g,
  )
}

async function applyForUser(user: any) {
  if (user.is_friend || user.has_pending_request) return
  const key = userKey(user)
  patchUser(key, { has_pending_request: true })
  applyingKeys.value = new Set(applyingKeys.value).add(key)
  try {
    await messageApi.applyFriend({
      applicant_type: data.profile.account_type,
      applicant_id: data.profile.account_id,
      recipient_type: user.account_type,
      recipient_id: user.account_id,
    })
    window.$message?.success?.('好友申请已发送')
  } catch {
    patchUser(key, { has_pending_request: false })
    window.$message?.error?.('好友申请发送失败')
  } finally {
    const next = new Set(applyingKeys.value)
    next.delete(key)
    applyingKeys.value = next
  }
}

async function applyJoinGroup(group: any) {
  if (group.is_member || group.has_pending_request) return
  patchGroup(group.id, { has_pending_request: true })
  try {
    await messageApi.applyJoinGroup({ group_id: group.id })
    window.$message?.success?.('入群申请已发送')
  } catch {
    patchGroup(group.id, { has_pending_request: false })
    window.$message?.error?.('入群申请发送失败')
  }
}

function closeModal() {
  show.value = false
  addSearchText.value = ''
  addSearchResults.value = []
  applyingKeys.value = new Set()
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :bordered="false"
    draggable
    title="添加好友 / 群聊"
    :mask-closable="false"
    style="width: min(700px, calc(100vw - 24px)); height: 75vh"
    content-style="display: flex; flex-direction: column; height: 65vh; padding: 0 20px 20px"
    @update:show="closeModal"
  >
    <div class="flex min-h-0 flex-1 flex-col gap-4">
      <NTabs v-model:value="addMode" type="segment" size="small">
        <NTabPane name="friend" tab="添加好友" />
        <NTabPane name="group" tab="添加群聊" />
      </NTabs>
      <NInputGroup>
        <NInputGroupLabel :style="{ color: themeVars.textColor3 }">
          <NovaIcon icon="icon-park-outline:search" :size="16" />
        </NInputGroupLabel>
        <NInput v-model:value="addSearchText" clearable :placeholder="addSearchPlaceholder" />
      </NInputGroup>
      <NScrollbar class="flex-1" style="max-height: calc(70vh - 140px)">
        <div v-if="addMode === 'friend'" class="pr-1">
          <NList v-if="addSearchText.trim() ? addSearchResults.length : false" hoverable>
            <NListItem
              v-for="user in addSearchResults"
              :key="`${user.account_type}-${user.account_id}`"
              class="message-list-item"
            >
              <div class="flex items-center gap-3 px-4 py-3">
                <NAvatar
                  v-if="user.avatar"
                  round
                  :size="40"
                  class="shrink-0"
                  :src="resolveFileUrl(user.avatar)"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="40" class="shrink-0">
                  {{ (user.name || user.nickname || user.account || '?').charAt(0) }}
                </NAvatar>
                <div class="min-w-0 flex-1">
                  <div class="message-ellipsis text-sm font-600">
                    {{ user.name || user.nickname || user.account }}
                  </div>
                  <div
                    class="message-ellipsis mt-1 text-xs"
                    :style="{ color: themeVars.textColor3 }"
                  >
                    {{ user.account ? '@' + user.account : user.signature || '-' }}
                  </div>
                </div>
                <NTag v-if="user.is_friend" :bordered="false" size="small" type="success">
                  已是好友
                </NTag>
                <NTag v-else-if="user.has_pending_request" :bordered="false" size="small">
                  已申请
                </NTag>
                <NButton
                  v-else
                  size="small"
                  tertiary
                  :loading="applyingKeys.has(userKey(user))"
                  @click="applyForUser(user)"
                >
                  申请好友
                </NButton>
              </div>
            </NListItem>
          </NList>
          <div
            v-else-if="addSearchLoading"
            class="py-8 text-center text-sm"
            :style="{ color: themeVars.textColor3 }"
          >
            搜索中...
          </div>
          <NEmpty v-else class="py-8" description="请输入关键词搜索用户" />
        </div>
        <div v-else-if="addMode === 'group'" class="pr-1">
          <NList v-if="addSearchText.trim() ? addSearchResults.length : false" hoverable>
            <NListItem v-for="group in addSearchResults" :key="group.id" class="message-list-item">
              <div class="flex items-center gap-3 px-4 py-3">
                <NAvatar
                  v-if="group.avatar"
                  round
                  :size="40"
                  class="shrink-0"
                  :src="resolveFileUrl(group.avatar)"
                  :img-props="avatarImgProps"
                />
                <NAvatar v-else round :size="40" class="shrink-0">
                  {{ (group.name || '?').charAt(0) }}
                </NAvatar>
                <div class="min-w-0 flex-1">
                  <div class="message-ellipsis text-sm font-600">
                    {{ group.name }}
                  </div>
                  <div
                    class="message-ellipsis mt-1 text-xs"
                    :style="{ color: themeVars.textColor3 }"
                  >
                    {{ group.member_count || 0 }} 人 · {{ group.description || '-' }}
                  </div>
                </div>
                <NTag v-if="group.is_member" :bordered="false" size="small" type="success">
                  已加入
                </NTag>
                <NTag v-else-if="group.has_pending_request" :bordered="false" size="small">
                  已申请
                </NTag>
                <NButton v-else size="small" tertiary @click="applyJoinGroup(group)">
                  加入群聊
                </NButton>
              </div>
            </NListItem>
          </NList>
          <div
            v-else-if="addSearchLoading"
            class="py-8 text-center text-sm"
            :style="{ color: themeVars.textColor3 }"
          >
            搜索中...
          </div>
          <NEmpty v-else class="py-8" description="请输入关键词搜索群组" />
        </div>
      </NScrollbar>
    </div>
  </NModal>
</template>
