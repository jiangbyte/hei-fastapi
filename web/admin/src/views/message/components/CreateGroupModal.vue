<script setup lang="ts">
import { resolveFileUrl } from '@/utils'
const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
import { computed, inject, ref } from 'vue'
import { messageApi } from '@/api'
import { MESSAGE_ACTIONS_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const data = inject(MESSAGE_DATA_KEY)!
const actions = inject(MESSAGE_ACTIONS_KEY)!

const show = defineModel<boolean>('show', { required: true })

const createGroupName = ref('')
const createGroupDesc = ref('')
/** friendship_id keys of invitees */
const createGroupInvitees = ref<string[]>([])
const showInviteFriendModal = ref(false)
const inviteSearchText = ref('')
const creating = ref(false)

const filteredInviteFriends = computed(() => {
  const keyword = inviteSearchText.value.trim().toLowerCase()
  if (!keyword) return data.friends
  return data.friends.filter(
    (f) =>
      (f.name ?? '').toLowerCase().includes(keyword) ||
      (f.nickname ?? '').toLowerCase().includes(keyword) ||
      (f.friend_account_type ?? '').toLowerCase().includes(keyword),
  )
})

function friendLabel(friendshipId: string) {
  const f = data.friends.find((x) => x.friendship_id === friendshipId)
  if (!f) return friendshipId
  const name = f.name || f.nickname || f.friend_account_id
  const tag = f.friend_account_type === 'PORTAL' ? '学生' : '管理员'
  return `${name}（${tag}）`
}

function toggleGroupInvitee(friendId: string) {
  const idx = createGroupInvitees.value.indexOf(friendId)
  if (idx >= 0) createGroupInvitees.value.splice(idx, 1)
  else createGroupInvitees.value.push(friendId)
}

function removeGroupInvitee(friendId: string) {
  const idx = createGroupInvitees.value.indexOf(friendId)
  if (idx >= 0) createGroupInvitees.value.splice(idx, 1)
}

function closeCreateGroup() {
  show.value = false
  createGroupName.value = ''
  createGroupDesc.value = ''
  createGroupInvitees.value = []
  inviteSearchText.value = ''
}

async function handleCreateGroup() {
  const name = createGroupName.value.trim()
  if (!name || creating.value) return

  creating.value = true
  try {
    const groupRes = await messageApi.createGroup({
      name,
      description: createGroupDesc.value.trim() || undefined,
    })
    const newGroup = groupRes?.data
    const invitees = createGroupInvitees.value
      .map((fid) => data.friends.find((f) => f.friendship_id === fid))
      .filter(Boolean)
      .map((f) => ({
        account_type: f!.friend_account_type,
        account_id: f!.friend_account_id,
      }))

    if (newGroup?.id && invitees.length) {
      await messageApi.addGroupMembers({
        group_id: newGroup.id,
        members: invitees,
      })
    }

    const groupsRes = await messageApi.groupList()
    if (groupsRes?.data) data.groups = groupsRes.data
    const convRes = await messageApi.conversationList()
    if (convRes?.data?.records) data.conversations = convRes.data.records
    closeCreateGroup()
    window.$message?.success?.(
      invitees.length ? `群聊创建成功，已邀请 ${invitees.length} 人` : '群聊创建成功',
    )

    if (newGroup?.id) {
      const groupConv = data.conversations.find((c: any) => c.group_id === newGroup.id)
      if (groupConv) {
        actions.openConversation(groupConv.id)
      }
    }
  } catch {
    window.$message?.error?.('创建群聊失败')
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :bordered="false"
    title="创建群聊"
    :mask-closable="false"
    style="width: min(480px, calc(100vw - 24px))"
    @after-leave="closeCreateGroup"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-3">
        <NAvatar round :size="48">群</NAvatar>
        <div class="min-w-0 flex-1">
          <NInput v-model:value="createGroupName" placeholder="群聊名称（必填）" size="large" />
        </div>
      </div>
      <NInput
        v-model:value="createGroupDesc"
        type="textarea"
        placeholder="群聊简介"
        :autosize="{ minRows: 2, maxRows: 4 }"
      />
      <div class="flex items-center justify-between">
        <span class="text-sm" style="color: var(--text-color-3)"
          >已邀请 {{ createGroupInvitees.length }} 人</span
        >
        <NButton size="small" @click="showInviteFriendModal = true">
          <template #icon>
            <NovaIcon icon="icon-park-outline:add" :size="14" />
          </template>
          邀请好友
        </NButton>
      </div>
      <div v-if="createGroupInvitees.length" class="flex flex-wrap gap-2">
        <NTag
          v-for="id in createGroupInvitees"
          :key="id"
          closable
          :bordered="false"
          size="small"
          @close="removeGroupInvitee(id)"
        >
          {{ friendLabel(id) }}
        </NTag>
      </div>
      <div class="flex justify-end gap-3 pt-2">
        <NButton @click="closeCreateGroup"> 取消 </NButton>
        <NButton
          type="primary"
          :loading="creating"
          :disabled="!createGroupName.trim()"
          @click="handleCreateGroup"
        >
          创建
        </NButton>
      </div>
    </div>
  </NModal>

  <NModal
    v-model:show="showInviteFriendModal"
    preset="card"
    :bordered="false"
    title="邀请好友"
    :mask-closable="false"
    style="width: min(400px, calc(100vw - 24px)); max-height: 60vh"
    content-style="display: flex; flex-direction: column; padding: 0 16px 16px; min-height: 0;"
  >
    <div class="flex min-h-0 flex-1 flex-col gap-3">
      <NInput v-model:value="inviteSearchText" clearable placeholder="搜索好友" size="small" />
      <NScrollbar class="flex-1" style="max-height: 40vh">
        <NList v-if="filteredInviteFriends.length" hoverable>
          <NListItem
            v-for="friend in filteredInviteFriends"
            :key="friend.friendship_id"
            class="message-list-item cursor-pointer"
            @click="toggleGroupInvitee(friend.friendship_id)"
          >
            <div class="flex items-center gap-3 px-2 py-2">
              <NCheckbox
                :checked="createGroupInvitees.includes(friend.friendship_id)"
                @click.stop="toggleGroupInvitee(friend.friendship_id)"
              />
              <NAvatar
                v-if="friend.avatar"
                round
                :size="36"
                class="shrink-0"
                :src="resolveFileUrl(friend.avatar)"
                :img-props="avatarImgProps"
              />
              <NAvatar v-else round :size="36" class="shrink-0">
                {{ (friend.name || friend.nickname || '?').charAt(0) }}
              </NAvatar>
              <div class="min-w-0 flex-1">
                <div class="message-ellipsis text-sm font-500">
                  {{ friend.name || friend.nickname }}
                  <NTag size="tiny" :bordered="false" class="ml-1">
                    {{ friend.friend_account_type === 'PORTAL' ? '学生' : '管理员' }}
                  </NTag>
                </div>
                <div class="message-ellipsis text-xs" style="color: var(--text-color-3)">
                  {{ friend.signature || '-' }}
                </div>
              </div>
            </div>
          </NListItem>
        </NList>
        <NEmpty v-else description="暂无好友" />
      </NScrollbar>
      <div class="flex justify-end">
        <NButton size="small" @click="showInviteFriendModal = false"> 确定 </NButton>
      </div>
    </div>
  </NModal>
</template>
