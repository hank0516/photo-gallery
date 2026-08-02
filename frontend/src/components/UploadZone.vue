<template>
  <div
    class="upload-zone"
    :class="{ dragging, hasFiles: queue.length > 0 }"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="fileInput.click()"
  >
    <input
      ref="fileInput"
      type="file"
      accept="image/*,.heic,.heif"
      multiple
      style="display:none"
      @change="onFileChange"
    />
    <div v-if="queue.length === 0" class="zone-hint">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      <p>拖放照片到此處，或點擊選擇</p>
      <span class="hint-sub">支援 JPG / PNG / WebP / HEIC，最大 {{ maxMb }} MB</span>
    </div>

    <div v-else class="queue" @click.stop>
      <div v-for="item in queue" :key="item.id" class="queue-item">
        <img :src="item.preview" class="q-thumb" />
        <div class="q-info">
          <span class="q-name">{{ item.file.name }}</span>
          <span class="q-size">{{ formatSize(item.file.size) }}</span>
          <div class="q-progress-wrap" v-if="item.status !== 'pending'">
            <div class="q-progress" :style="{ width: item.progress + '%' }" :class="item.status"></div>
          </div>
          <span class="q-status" :class="item.status">
            {{ statusLabel(item) }}
          </span>
        </div>
        <button class="q-remove" @click="remove(item.id)" :disabled="item.status === 'uploading'">✕</button>
      </div>

      <div class="queue-footer" @click.stop>
        <button class="btn-secondary" @click="fileInput.click()">+ 更多</button>
        <button
          class="btn-primary"
          :disabled="uploading || pendingCount === 0"
          @click="uploadAll"
        >
          {{ uploading ? `上傳中… (${doneCount}/${queue.length})` : `上傳 ${pendingCount} 張` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/api'

const props = defineProps({
  albumId: { type: Number, required: true },
  maxMb: { type: Number, default: 50 },
})
const emit = defineEmits(['uploaded'])

const fileInput = ref(null)
const dragging = ref(false)
const queue = ref([])
const uploading = ref(false)

const pendingCount = computed(() => queue.value.filter(i => i.status === 'pending').length)
const doneCount = computed(() => queue.value.filter(i => i.status === 'done').length)

function addFiles(files) {
  dragging.value = false
  for (const f of files) {
    if (!f.type.startsWith('image/') && !f.name.match(/\.(heic|heif)$/i)) continue
    const id = Math.random().toString(36).slice(2)
    const preview = URL.createObjectURL(f)
    queue.value.push({ id, file: f, preview, status: 'pending', progress: 0, error: null })
  }
}

function onDrop(e) { addFiles(e.dataTransfer.files) }
function onFileChange(e) { addFiles(e.target.files); e.target.value = '' }

function remove(id) {
  const item = queue.value.find(i => i.id === id)
  if (item) URL.revokeObjectURL(item.preview)
  queue.value = queue.value.filter(i => i.id !== id)
}

async function uploadAll() {
  uploading.value = true
  const pending = queue.value.filter(i => i.status === 'pending')
  for (const item of pending) {
    item.status = 'uploading'
    item.progress = 0
    try {
      const form = new FormData()
      form.append('file', item.file)
      const { data } = await api.post(`/albums/${props.albumId}/photos`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: e => {
          item.progress = Math.round((e.loaded / e.total) * 100)
        },
      })
      item.status = 'done'
      item.progress = 100
      emit('uploaded', data)
    } catch (e) {
      item.status = 'error'
      item.error = e.response?.data?.detail || '上傳失敗'
    }
  }
  uploading.value = false
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function statusLabel(item) {
  if (item.status === 'pending') return '等待中'
  if (item.status === 'uploading') return `${item.progress}%`
  if (item.status === 'done') return '完成'
  return item.error || '錯誤'
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed #333;
  border-radius: 10px;
  padding: 24px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  min-height: 120px;
}
.upload-zone.dragging {
  border-color: #5c6bc0;
  background: rgba(92, 107, 192, 0.08);
}
.upload-zone.hasFiles { cursor: default; }
.zone-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #555;
  text-align: center;
  min-height: 100px;
}
.zone-hint p { margin: 0; font-size: 15px; }
.hint-sub { font-size: 12px; color: #444; }
.queue {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 8px 10px;
}
.q-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}
.q-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.q-name {
  font-size: 13px;
  color: #ccc;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.q-size { font-size: 11px; color: #555; }
.q-progress-wrap {
  height: 3px;
  background: #333;
  border-radius: 2px;
  overflow: hidden;
}
.q-progress {
  height: 100%;
  background: #5c6bc0;
  border-radius: 2px;
  transition: width 0.2s;
}
.q-progress.done { background: #388e3c; }
.q-progress.error { background: #ef5350; }
.q-status {
  font-size: 11px;
  color: #666;
}
.q-status.done { color: #66bb6a; }
.q-status.error { color: #ef5350; }
.q-remove {
  background: transparent;
  border: none;
  color: #555;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  flex-shrink: 0;
}
.q-remove:hover:not(:disabled) { color: #ef5350; }
.q-remove:disabled { opacity: 0.3; }
.queue-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 8px;
}
.btn-primary {
  padding: 8px 18px;
  background: #5c6bc0;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.btn-primary:hover:not(:disabled) { background: #7986cb; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-secondary {
  padding: 8px 14px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #aaa;
  cursor: pointer;
  font-size: 13px;
}
.btn-secondary:hover { background: #333; }
</style>
