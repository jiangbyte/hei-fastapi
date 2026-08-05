<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useThemeVars } from 'naive-ui'
import { useImCenterStore } from '@/stores'
import MessageCenter from '@/views/message/MessageCenter.vue'

const imCenterStore = useImCenterStore()
const { visible } = storeToRefs(imCenterStore)
const themeVars = useThemeVars()

function onUpdateShow(v: boolean) {
  if (!v) imCenterStore.close()
}
</script>

<template>
  <NModal
    v-model:show="visible"
    :mask-closable="true"
    :auto-focus="false"
    :trap-focus="false"
    display-directive="show"
    transform-origin="center"
    @update:show="onUpdateShow"
  >
    <div
      class="im-center-shell"
      :style="{
        backgroundColor: themeVars.cardColor,
        color: themeVars.textColor1,
        boxShadow: themeVars.boxShadow2,
      }"
    >
      <header
        class="im-center-shell__header"
        :style="{ borderBottomColor: themeVars.borderColor }"
      >
        <span class="text-sm font-600">消息中心</span>
        <NButton text size="small" aria-label="关闭" @click="imCenterStore.close()">
          <template #icon>
            <NovaIcon icon="icon-park-outline:close" :size="18" />
          </template>
        </NButton>
      </header>
      <div class="im-center-shell__body">
        <MessageCenter modal />
      </div>
    </div>
  </NModal>
</template>

<style scoped>
.im-center-shell {
  width: 1120px;
  height: 620px;
  max-width: calc(100vw - 48px);
  max-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 10px;
}
.im-center-shell__header {
  flex: 0 0 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  border-bottom: 1px solid;
}
.im-center-shell__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}
</style>
