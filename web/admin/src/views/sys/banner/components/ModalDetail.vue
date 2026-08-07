<!-- Author: Charlie -->

<script setup lang="ts">
import { bannerApi } from '@/api'
import { createTagColor, displayValue, formatDateTime, resolveFileUrl } from '@/utils'
import { computed, reactive } from 'vue'
import { dictTypeData, dictTypeColor } from '@/utils/dict'

const state = reactive({
  showModal: false,
  loading: false,
  banner: {} as any,
})

const imageAlt = computed(() => state.banner?.title ?? '图片')
const imageUrl = computed(() => resolveFileUrl(state.banner?.image))

async function openModal(id: string) {
  state.banner = {}
  state.showModal = true
  await fetchDetail(id)
}

async function fetchDetail(id: string) {
  state.loading = true
  try {
    const response = await bannerApi.detail({ id })
    state.banner = response.data
  } finally {
    state.loading = false
  }
}

defineExpose({
  openModal,
})
</script>

<template>
  <NModal
    v-model:show="state.showModal"
    preset="card"
    draggable
    :mask-closable="false"
    :title="'展示图详情'"
    style="width: 620px"
  >
    <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
      <NSpin :show="state.loading">
        <NDescriptions label-placement="left" bordered :column="1">
          <NDescriptionsItem :label="'标题'">
            {{ displayValue(state.banner.title) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'图片'">
            <NImage
              v-if="state.banner.image"
              class="banner-detail-image"
              :src="imageUrl"
              :alt="imageAlt"
              :width="220"
              :height="140"
              object-fit="cover"
            />
            <template v-else> - </template>
          </NDescriptionsItem>
          <NDescriptionsItem :label="'目标URL'">
            {{ displayValue(state.banner.url) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'链接类型'">
            {{ dictTypeData('BANNER_LINK_TYPE', state.banner.link_type) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'分类'">
            {{ dictTypeData('BANNER_CATEGORY', state.banner.category) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'类型'">
            {{ dictTypeData('BANNER_TYPE', state.banner.type) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'岗位'">
            {{ dictTypeData('BANNER_POSITION', state.banner.position) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'展示范围'">
            <NTag
              :color="
                createTagColor(dictTypeColor('BANNER_DISPLAY_SCOPE', state.banner.display_scope))
              "
              :bordered="false"
            >
              {{ dictTypeData('BANNER_DISPLAY_SCOPE', state.banner.display_scope) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem :label="'排序'">
            {{ displayValue(state.banner.sort) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'互动次数'">
            {{ displayValue(state.banner.interaction_count) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'状态'">
            <NTag
              :color="createTagColor(dictTypeColor('COMMON_STATUS', state.banner.status))"
              :bordered="false"
            >
              {{ dictTypeData('COMMON_STATUS', state.banner.status) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem :label="'开始时间'">
            {{ formatDateTime(state.banner.start_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'结束时间'">
            {{ formatDateTime(state.banner.end_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'摘要'">
            {{ displayValue(state.banner.summary) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'描述'">
            {{ displayValue(state.banner.description) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'创建人'">
            {{ displayValue(state.banner.created_name) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'创建时间'">
            {{ formatDateTime(state.banner.created_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'更新人'">
            {{ displayValue(state.banner.updated_name) }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="'更新时间'">
            {{ formatDateTime(state.banner.updated_at) }}
          </NDescriptionsItem>
        </NDescriptions>
      </NSpin>
    </NScrollbar>
  </NModal>
</template>

<style scoped>
.banner-detail-image {
  border-radius: 6px;
}
</style>
