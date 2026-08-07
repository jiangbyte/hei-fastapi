<!-- Author: Charlie -->

<script setup lang="ts">
import { computed, inject } from 'vue'
import { useThemeVars } from 'naive-ui'
import { resolveFileUrl } from '@/utils'
import { MESSAGE_ACTIONS_KEY, MESSAGE_UI_STATE_KEY, MESSAGE_DATA_KEY } from '../provide-keys'

const themeVars = useThemeVars()
const data = inject(MESSAGE_DATA_KEY)!
const actions = inject(MESSAGE_ACTIONS_KEY)!
const ui = inject(MESSAGE_UI_STATE_KEY)!

const avatarImgProps = { referrerPolicy: 'no-referrer' } as any
const avatarUrl = computed(() => resolveFileUrl(data.profile?.avatar))
</script>

<template>
  <NModal
    v-model:show="ui.showProfileModal.value"
    preset="card"
    draggable
    :bordered="false"
    title="个人信息"
    style="width: min(460px, calc(100vw - 32px))"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-3">
        <NAvatar
          v-if="avatarUrl"
          round
          :size="56"
          :src="avatarUrl"
          :img-props="avatarImgProps"
          class="shrink-0"
        />
        <NAvatar v-else round :size="56" class="shrink-0">
          <NovaIcon icon="icon-park-outline:user" :size="28" />
        </NAvatar>
        <div class="min-w-0">
          <div class="text-base font-600">
            {{ data.profile?.nickname }}
          </div>
          <div class="mt-1 text-xs" :style="{ color: themeVars.textColor3 }">
            {{ data.profile?.title }}
          </div>
        </div>
      </div>
      <NDescriptions :column="1" label-placement="left" size="small">
        <NDescriptionsItem label="账号">
          {{ data.profile?.account }}
        </NDescriptionsItem>
        <NDescriptionsItem label="角色">
          {{ data.profile?.role }}
        </NDescriptionsItem>
        <NDescriptionsItem label="部门">
          {{ data.profile?.department }}
        </NDescriptionsItem>
      </NDescriptions>
      <NFlex justify="center" :wrap="true" :size="12">
        <NButton type="primary" @click="actions.goProfileCenter()"> 个人中心 </NButton>
        <NButton tertiary type="error" @click="actions.handleLogout()"> 退出登录 </NButton>
      </NFlex>
    </div>
  </NModal>
</template>
