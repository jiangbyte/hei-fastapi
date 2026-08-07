<!-- Author: Charlie -->

<script setup lang="ts">
import { inject, computed, ref } from 'vue'
import { useThemeVars } from 'naive-ui'
import { renderIcon } from '@/utils/icon'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY } from '../provide-keys'
import ChatList from './ChatList.vue'
import ContactList from './ContactList.vue'
import NoticeList from './NoticeList.vue'
import SearchResults from './SearchResults.vue'
import CreateGroupModal from './CreateGroupModal.vue'

const themeVars = useThemeVars()
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const normalizedSearch = computed(() => ui.searchText.value.trim().toLowerCase())
const hasSearchKeyword = computed(() => normalizedSearch.value.length > 0)
const showCreateGroupModal = ref(false)
function handleOpenCreateGroup() {
  showCreateGroupModal.value = true
}
function handleDropdownSelect(key: string) {
  if (key === 'add-friend') {
    actions.openAddModal()
    return
  }
  if (key === 'join-group') {
    actions.openAddModal('group')
    return
  }
  if (key === 'create-group') {
    handleOpenCreateGroup()
    return
  }
}
</script>

<template>
  <NCard
    :bordered="false"
    class="h-full min-h-0 overflow-hidden shadow-sm"
    :content-style="{ height: '100%', padding: '0' }"
  >
    <div class="flex h-full min-h-0 flex-col">
      <div
        v-show="ui.activeSection.value === 'chat' || ui.activeSection.value === 'contacts'"
        class="border-b px-4 py-3"
        :style="{ borderColor: themeVars.borderColor }"
      >
        <div class="flex items-center gap-2">
          <NInputGroup class="flex-1">
            <NInputGroupLabel :style="{ color: themeVars.textColor3 }">
              <NovaIcon icon="icon-park-outline:search" :size="16" />
            </NInputGroupLabel>
            <NInput
              v-model:value="ui.searchText.value"
              clearable
              placeholder="搜索群组 / 用户 / 对话"
            />
          </NInputGroup>
          <NDropdown
            v-if="ui.activeSection.value === 'contacts'"
            trigger="click"
            placement="bottom-end"
            :options="[
              {
                key: 'add-friend',
                label: '添加好友',
                icon: renderIcon('icon-park-outline:add-one'),
              },
              { key: 'join-group', label: '添加群聊', icon: renderIcon('icon-park-outline:group') },
              { key: 'create-group', label: '创建群聊', icon: renderIcon('icon-park-outline:add') },
            ]"
            @select="handleDropdownSelect"
          >
            <NButton text size="small" class="px-2" style="color: var(--text-color-3)">
              <template #icon>
                <NovaIcon icon="icon-park-outline:add" :size="18" />
              </template>
            </NButton>
          </NDropdown>
        </div>
      </div>

      <SearchResults v-if="hasSearchKeyword" :keyword="normalizedSearch" />

      <ChatList v-else-if="ui.activeSection.value === 'chat'" />

      <NoticeList v-else-if="ui.activeSection.value === 'notice'" />

      <ContactList v-else-if="ui.activeSection.value === 'contacts'" />
      <CreateGroupModal v-model:show="showCreateGroupModal" />
    </div>
  </NCard>
</template>
