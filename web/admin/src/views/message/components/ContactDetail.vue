<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'
import { useThemeVars } from 'naive-ui'
import { resolveFileUrl } from '@/utils'
import { messageApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { Friend, Group, GroupMember } from '../types'
import { MESSAGE_UI_STATE_KEY } from '../provide-keys'

const props = defineProps<{
  friend: Friend | null
  group: Group | null
  hint: string
}>()

const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
const avatarUrl = computed(
  () => resolveFileUrl(props.friend?.avatar) || resolveFileUrl(props.group?.avatar) || undefined,
)

const emit = defineEmits<{
  chat: []
  removeFriend: []
  leaveGroup: []
  dissolveGroup: []
  back: []
}>()

const themeVars = useThemeVars()
const ui = inject(MESSAGE_UI_STATE_KEY)!
const authStore = useAuthStore()

const members = ref<GroupMember[]>([])
const membersLoading = ref(false)
const actionLoading = ref(false)

const myAccountType = computed(() => String(authStore.userInfo?.accountType || 'ADMIN'))
const myAccountId = computed(() => String(authStore.userInfo?.accountId || ''))

const isGroupOwner = computed(() => {
  if (!props.group) return false
  return (
    props.group.owner_account_type === myAccountType.value &&
    props.group.owner_account_id === myAccountId.value
  )
})

const isGroupAdmin = computed(() => {
  if (!props.group) return false
  if (isGroupOwner.value) return true
  return members.value.some(
    (m) =>
      m.account_type === myAccountType.value &&
      m.account_id === myAccountId.value &&
      (m.role === 'ADMIN' || m.role === 'OWNER'),
  )
})

watch(
  () => props.group?.id,
  async (id) => {
    members.value = []
    if (!id) return
    membersLoading.value = true
    try {
      const res = await messageApi.groupMemberList(id)
      members.value = res?.data ?? []
    } catch {
      members.value = []
    } finally {
      membersLoading.value = false
    }
  },
  { immediate: true },
)

function typeLabel(accountType: string) {
  return accountType === 'PORTAL' ? '学生' : '管理员'
}

function roleLabel(role: string) {
  if (role === 'OWNER') return '群主'
  if (role === 'ADMIN') return '管理员'
  return '成员'
}

async function setRole(member: GroupMember, role: string) {
  if (!props.group || actionLoading.value) return
  actionLoading.value = true
  try {
    await messageApi.setGroupMemberRole({
      group_id: props.group.id,
      account_type: member.account_type,
      account_id: member.account_id,
      role,
    })
    member.role = role
    window.$message?.success?.(role === 'ADMIN' ? '已设为管理员' : '已取消管理员')
  } catch {
    window.$message?.error?.('设置角色失败')
  } finally {
    actionLoading.value = false
  }
}

async function kickMember(member: GroupMember) {
  if (!props.group || actionLoading.value) return
  actionLoading.value = true
  try {
    await messageApi.removeGroupMember({
      group_id: props.group.id,
      account_type: member.account_type,
      account_id: member.account_id,
    })
    members.value = members.value.filter(
      (m) => !(m.account_type === member.account_type && m.account_id === member.account_id),
    )
    window.$message?.success?.('已移除成员')
  } catch {
    window.$message?.error?.('移除成员失败')
  } finally {
    actionLoading.value = false
  }
}
</script>

<template>
  <NCard
    :bordered="false"
    class="h-full min-h-0 overflow-hidden shadow-sm"
    :content-style="{ height: '100%', padding: '0' }"
  >
    <template v-if="friend || group">
      <div class="flex h-full min-h-0 flex-col">
        <NScrollbar class="h-full">
          <div class="mx-auto flex w-full max-w-[460px] flex-col gap-4 px-4 py-6">
            <div v-if="ui.isMobile.value" class="flex justify-start">
              <NButton text size="small" @click="emit('back')">
                <template #icon>
                  <NovaIcon icon="icon-park-outline:arrow-left" :size="18" />
                </template>
              </NButton>
            </div>
            <NAlert v-if="hint" type="success" :bordered="false">
              {{ hint }}
            </NAlert>
            <div class="flex items-center gap-3">
              <NAvatar
                v-if="avatarUrl"
                round
                :size="64"
                class="shrink-0"
                :src="avatarUrl"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="64" class="shrink-0">
                {{ (friend?.name || group?.name || '?').charAt(0) }}
              </NAvatar>
              <div class="min-w-0 text-left">
                <div class="flex items-center gap-2 truncate text-lg font-600">
                  <span class="truncate">{{ friend?.name || group?.name }}</span>
                  <NTag v-if="friend" size="small" :bordered="false">
                    {{ typeLabel(friend.friend_account_type) }}
                  </NTag>
                </div>
                <div class="truncate text-xs" :style="{ color: themeVars.textColor3 }">
                  {{ friend ? friend.signature || '-' : group?.description || '-' }}
                </div>
              </div>
            </div>
            <NDescriptions :column="1" label-placement="left" size="small">
              <template v-if="friend">
                <NDescriptionsItem label="备注">
                  {{ friend.remark || '-' }}
                </NDescriptionsItem>
                <NDescriptionsItem label="类型">
                  {{ typeLabel(friend.friend_account_type) }}
                </NDescriptionsItem>
                <NDescriptionsItem label="签名">
                  {{ friend.signature || '-' }}
                </NDescriptionsItem>
              </template>
              <template v-else-if="group">
                <NDescriptionsItem label="成员"> {{ group.member_count }} 人 </NDescriptionsItem>
                <NDescriptionsItem label="说明">
                  {{ group.description || '-' }}
                </NDescriptionsItem>
                <NDescriptionsItem label="状态">
                  {{ group.status }}
                </NDescriptionsItem>
              </template>
            </NDescriptions>

            <template v-if="group">
              <div class="text-sm font-600">群成员</div>
              <NSpin :show="membersLoading">
                <div class="flex flex-col gap-2">
                  <div
                    v-for="m in members"
                    :key="`${m.account_type}:${m.account_id}`"
                    class="flex items-center gap-2 rounded-lg px-2 py-2"
                    style="background: var(--n-color-embedded)"
                  >
                    <NAvatar
                      v-if="m.profile_avatar"
                      round
                      :size="32"
                      :src="resolveFileUrl(m.profile_avatar)"
                      :img-props="avatarImgProps"
                    />
                    <NAvatar v-else round :size="32">
                      {{ (m.profile_name || m.nickname || '?').charAt(0) }}
                    </NAvatar>
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-sm">
                        {{ m.profile_name || m.nickname || m.account_id }}
                      </div>
                      <div class="text-xs" :style="{ color: themeVars.textColor3 }">
                        {{ typeLabel(m.account_type) }} · {{ roleLabel(m.role) }}
                      </div>
                    </div>
                    <template v-if="isGroupOwner && m.role !== 'OWNER'">
                      <NButton
                        v-if="m.role !== 'ADMIN'"
                        size="tiny"
                        quaternary
                        @click="setRole(m, 'ADMIN')"
                      >
                        设管
                      </NButton>
                      <NButton v-else size="tiny" quaternary @click="setRole(m, 'MEMBER')">
                        取消管
                      </NButton>
                      <NButton size="tiny" quaternary type="error" @click="kickMember(m)">
                        移除
                      </NButton>
                    </template>
                    <template v-else-if="isGroupAdmin && m.role === 'MEMBER'">
                      <NButton size="tiny" quaternary type="error" @click="kickMember(m)">
                        移除
                      </NButton>
                    </template>
                  </div>
                  <NEmpty v-if="!membersLoading && !members.length" description="暂无成员" />
                </div>
              </NSpin>
            </template>

            <NFlex justify="center" :wrap="true" :size="12">
              <NButton type="primary" @click="emit('chat')"> 发消息 </NButton>
              <NButton v-if="friend" tertiary type="error" @click="emit('removeFriend')">
                删除好友
              </NButton>
              <template v-else>
                <NButton v-if="isGroupOwner" tertiary type="error" @click="emit('dissolveGroup')">
                  解散群聊
                </NButton>
                <NButton v-else tertiary type="error" @click="emit('leaveGroup')"> 退出群聊 </NButton>
              </template>
            </NFlex>
          </div>
        </NScrollbar>
      </div>
    </template>
    <NEmpty v-else class="h-full flex items-center justify-center" description="请选择联系人" />
  </NCard>
</template>
