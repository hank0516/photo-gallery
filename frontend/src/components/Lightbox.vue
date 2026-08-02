<template>
  <teleport to="body">
    <div v-if="visible" class="lightbox" @keydown="onKey" tabindex="0" ref="boxEl">
      <!-- Top bar -->
      <div class="lb-topbar">
        <span class="lb-counter">{{ currentIndex + 1 }} / {{ photos.length }}</span>
        <div class="lb-topbar-actions">
          <button class="lb-icon-btn" @click="showInfo = !showInfo" title="詳情">ⓘ</button>
          <a :href="`/api/photo-gallery/photos/${current?.id}/download`" target="_blank" class="lb-icon-btn" title="下載">↓</a>
          <button v-if="myRole === 'admin'" class="lb-icon-btn danger" :disabled="deleting" @click="deletePhoto" title="刪除">🗑</button>
          <button class="lb-icon-btn" @click="$emit('close')" title="關閉 (Esc)">✕</button>
        </div>
      </div>

      <!-- Main area -->
      <div class="lb-main">
        <!-- Prev -->
        <button class="lb-nav lb-prev" :disabled="currentIndex === 0" @click="go(-1)">‹</button>

        <!-- Image -->
        <div class="lb-img-wrap" @click.self="$emit('close')">
          <img
            v-if="current"
            :src="current.thumb_800_url"
            :alt="current.caption || current.filename"
            class="lb-img"
            :class="{ loading: imgLoading }"
            @load="imgLoading = false"
            @loadstart="imgLoading = true"
          />
          <div v-if="imgLoading" class="lb-spinner"></div>
        </div>

        <!-- Next -->
        <button class="lb-nav lb-next" :disabled="currentIndex === photos.length - 1" @click="go(1)">›</button>

        <!-- Desktop side panel -->
        <div v-if="current && showInfo" class="lb-details lb-details-side">
          <div v-if="current.caption" class="lb-caption">{{ current.caption }}</div>
          <div class="lb-filename">{{ current.filename }}</div>
          <div v-if="current.exif_date_taken" class="lb-meta">
            <span class="meta-label">拍攝時間</span>
            <span>{{ formatDate(current.exif_date_taken) }}</span>
          </div>
          <div v-if="current.width" class="lb-meta">
            <span class="meta-label">尺寸</span>
            <span>{{ current.width }} × {{ current.height }}</span>
          </div>
        </div>
      </div>

      <!-- Mobile bottom sheet -->
      <div v-if="current && showInfo" class="lb-details lb-details-bottom">
        <div v-if="current.caption" class="lb-caption">{{ current.caption }}</div>
        <div class="lb-filename">{{ current.filename }}</div>
        <div v-if="current.exif_date_taken" class="lb-meta">
          <span class="meta-label">拍攝時間</span>
          <span>{{ formatDate(current.exif_date_taken) }}</span>
        </div>
        <div v-if="current.width" class="lb-meta">
          <span class="meta-label">尺寸</span>
          <span>{{ current.width }} × {{ current.height }}</span>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/services/api'

const props = defineProps({
  visible: Boolean,
  photos: { type: Array, default: () => [] },
  startIndex: { type: Number, default: 0 },
  myRole: { type: String, default: '' },
})
const emit = defineEmits(['close', 'update:startIndex', 'deleted'])

const currentIndex = ref(props.startIndex)
const imgLoading = ref(false)
const deleting = ref(false)
const showInfo = ref(false)
const boxEl = ref(null)

const current = computed(() => props.photos[currentIndex.value] ?? null)

watch(() => props.startIndex, v => { currentIndex.value = v })
watch(() => props.visible, v => {
  if (v) {
    showInfo.value = false
    nextTick(() => boxEl.value?.focus())
  }
})

function go(delta) {
  const next = currentIndex.value + delta
  if (next < 0 || next >= props.photos.length) return
  imgLoading.value = true
  currentIndex.value = next
  emit('update:startIndex', next)
}

function onKey(e) {
  if (e.key === 'ArrowLeft') go(-1)
  else if (e.key === 'ArrowRight') go(1)
  else if (e.key === 'Escape') emit('close')
}

async function deletePhoto() {
  if (!current.value) return
  if (!confirm(`確定要刪除「${current.value.filename}」？`)) return
  deleting.value = true
  try {
    await api.delete(`/photos/${current.value.id}`)
    emit('deleted', current.value.id)
    if (props.photos.length <= 1) {
      emit('close')
    } else {
      const nextIdx = Math.min(currentIndex.value, props.photos.length - 2)
      currentIndex.value = nextIdx
      emit('update:startIndex', nextIdx)
    }
  } catch (e) {
    alert(e.response?.data?.detail || '刪除失敗')
  } finally {
    deleting.value = false
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  background: #000;
  display: flex;
  flex-direction: column;
  z-index: 200;
  outline: none;
}

/* Top bar */
.lb-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(0,0,0,0.6);
  flex-shrink: 0;
  z-index: 10;
}
.lb-counter { font-size: 13px; color: #888; }
.lb-topbar-actions { display: flex; gap: 8px; align-items: center; }
.lb-icon-btn {
  background: transparent;
  border: none;
  color: #aaa;
  font-size: 18px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 4px;
  line-height: 1;
  text-decoration: none;
  display: flex;
  align-items: center;
}
.lb-icon-btn:hover:not(:disabled) { color: #fff; background: rgba(255,255,255,0.1); }
.lb-icon-btn:disabled { opacity: 0.3; cursor: default; }
.lb-icon-btn.danger:hover:not(:disabled) { color: #ef5350; background: rgba(239,83,80,0.15); }

/* Main area: nav + image + side panel */
.lb-main {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 0;
  overflow: hidden;
}

.lb-nav {
  flex-shrink: 0;
  width: 48px;
  height: 100%;
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.3);
  font-size: 48px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  user-select: none;
  transition: color 0.15s, background 0.15s;
}
.lb-nav:hover:not(:disabled) { color: #fff; background: rgba(255,255,255,0.05); }
.lb-nav:disabled { opacity: 0.1; cursor: default; }

.lb-img-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-width: 0;
  position: relative;
}
.lb-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: opacity 0.15s;
}
.lb-img.loading { opacity: 0; }
.lb-spinner {
  position: absolute;
  width: 36px;
  height: 36px;
  border: 3px solid #222;
  border-top-color: #888;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Side panel — desktop only */
.lb-details-side {
  width: 200px;
  flex-shrink: 0;
  height: 100%;
  overflow-y: auto;
  padding: 20px 14px;
  background: rgba(255,255,255,0.04);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Bottom sheet — mobile only */
.lb-details-bottom {
  display: none;
  padding: 14px 16px;
  background: rgba(20,20,20,0.95);
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  border-top: 1px solid #222;
}

.lb-caption { font-size: 14px; color: #e0e0e0; }
.lb-filename { font-size: 11px; color: #555; word-break: break-all; }
.lb-meta { display: flex; flex-direction: column; gap: 2px; font-size: 13px; color: #aaa; }
.meta-label { font-size: 10px; color: #555; text-transform: uppercase; }

/* Mobile */
@media (max-width: 640px) {
  .lb-details-side { display: none; }
  .lb-details-bottom { display: flex; }
  .lb-nav { width: 40px; font-size: 36px; }
}
</style>
