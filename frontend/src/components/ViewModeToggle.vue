<template>
  <div class="view-toggle">
    <button
      v-for="mode in modes"
      :key="mode.value"
      :class="{ active: modelValue === mode.value }"
      :title="mode.label"
      @click="$emit('update:modelValue', mode.value)"
    >
      <component :is="mode.icon" />
    </button>
  </div>
</template>

<script setup>
import { h } from 'vue'

defineProps({ modelValue: { type: String, default: 'small-grid' } })
defineEmits(['update:modelValue'])

const SmallGrid = () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'currentColor' }, [
  h('rect', { x: 2, y: 2, width: 9, height: 9 }),
  h('rect', { x: 13, y: 2, width: 9, height: 9 }),
  h('rect', { x: 2, y: 13, width: 9, height: 9 }),
  h('rect', { x: 13, y: 13, width: 9, height: 9 }),
])

const LargeGrid = () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('rect', { x: 3, y: 3, width: 8, height: 8 }),
  h('rect', { x: 13, y: 3, width: 8, height: 8 }),
  h('rect', { x: 3, y: 13, width: 8, height: 8 }),
  h('rect', { x: 13, y: 13, width: 8, height: 8 }),
])

const ListView = () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('line', { x1: 3, y1: 6, x2: 21, y2: 6 }),
  h('line', { x1: 3, y1: 12, x2: 21, y2: 12 }),
  h('line', { x1: 3, y1: 18, x2: 21, y2: 18 }),
])

const modes = [
  { value: 'small-grid', label: '小縮圖', icon: SmallGrid },
  { value: 'large-grid', label: '大縮圖', icon: LargeGrid },
  { value: 'list', label: '列表', icon: ListView },
]
</script>

<style scoped>
.view-toggle {
  display: flex;
  gap: 2px;
  background: #2a2a2a;
  border-radius: 6px;
  padding: 3px;
}
.view-toggle button {
  background: transparent;
  border: none;
  border-radius: 4px;
  padding: 5px 8px;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  transition: background 0.1s, color 0.1s;
}
.view-toggle button:hover { color: #ccc; background: #333; }
.view-toggle button.active { background: #444; color: #e0e0e0; }
</style>
