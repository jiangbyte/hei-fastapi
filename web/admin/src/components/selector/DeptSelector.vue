<!-- Author: Charlie -->

<script setup lang="tsx">
import { deptApi } from '@/api'
import { NTree } from 'naive-ui'
import { reactive, watch } from 'vue'

interface DeptNode {
  id: string
  label: string
  isLeaf?: boolean
  children?: DeptNode[]
}

const props = withDefaults(
  defineProps<{
    visible: boolean
    mode?: 'single' | 'multiple'
    title?: string
    selected?: string[]
  }>(),
  { mode: 'single', title: '选择部门', selected: () => [] },
)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  select: [value: { id: string; name: string }]
  'update:selected': [value: string[]]
  confirm: [value: string[]]
}>()

const state = reactive({
  loading: false,
  treeData: [] as DeptNode[],
  checkedKeys: [] as string[],
  selectedNode: null as DeptNode | null,
})

watch(
  () => props.visible,
  (val) => {
    if (val) {
      state.checkedKeys = [...props.selected]
      state.selectedNode = null
      loadTree()
    }
  },
)

function buildTree(tree: any[]): DeptNode[] {
  return (tree || []).map((item: any) => ({
    id: item.id,
    label: item.name || item.label || item.id,
    isLeaf: !item.children || item.children.length === 0,
    children: item.children ? buildTree(item.children) : undefined,
  }))
}

async function loadTree() {
  state.loading = true
  try {
    const res = await deptApi.tree()
    state.treeData = buildTree(res.data ?? [])
  } catch {
    state.treeData = []
  } finally {
    state.loading = false
  }
}

function handleUpdateKeys(keys: Array<string | number>) {
  const strKeys = keys.map(String)
  state.checkedKeys = strKeys
  if (props.mode === 'single' && strKeys.length > 0) {
    const findNode = (nodes: DeptNode[]): DeptNode | null => {
      for (const n of nodes) {
        if (n.id === strKeys[0]) return n
        if (n.children) {
          const found = findNode(n.children)
          if (found) return found
        }
      }
      return null
    }
    const node = findNode(state.treeData)
    if (node) {
      emit('select', { id: node.id, name: node.label })
    }
    close()
  }
}

function handleConfirm() {
  emit('update:selected', [...state.checkedKeys])
  emit('confirm', [...state.checkedKeys])
  close()
}

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <NDrawer
    :show="visible"
    placement="right"
    :width="440"
    :mask-closable="false"
    @update:show="(v: boolean) => emit('update:visible', v)"
  >
    <NDrawerContent :title="title" closable>
      <NSpin :show="state.loading">
        <NTree
          :data="state.treeData"
          :default-checked-keys="state.checkedKeys"
          :checkable="mode === 'multiple'"
          :selectable="mode === 'single'"
          block-line
          cascade
          @update:checked-keys="handleUpdateKeys"
          @update:selected-keys="(keys) => keys.length && handleUpdateKeys(keys)"
        />
      </NSpin>
      <template v-if="mode === 'multiple'" #footer>
        <NSpace justify="end">
          <NButton @click="close"> 关闭 </NButton>
          <NButton type="primary" @click="handleConfirm"> 确认 </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
