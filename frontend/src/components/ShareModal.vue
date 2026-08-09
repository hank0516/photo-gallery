<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h2>分享連結</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Create new link -->
      <div class="create-section">
        <label class="create-label">建立新連結，有效天數：</label>
        <div class="create-row">
          <select v-model="expiresDays" class="days-select">
            <option :value="7">7 天</option>
            <option :value="14">14 天</option>
            <option :value="30">30 天</option>
            <option :value="90">90 天</option>
          </select>
          <button class="btn-primary" :disabled="creating" @click="createLink">
            {{ creating ? '建立中…' : '建立連結' }}
          </button>
        </div>
        <p v-if="createError" class="error-msg">{{ createError }}</p>
      </div>

      <!-- Links list -->
      <div class="links-section">
        <div v-if="loading" class="status-msg">載入中…</div>
        <div v-else-if="links.length === 0" class="status-msg">尚無分享連結</div>
        <div v-else class="links-list">
          <div v-for="link in links" :key="link.token" class="link-item" :class="{ inactive: link.is_revoked || link.is_expired }">
            <div class="link-info">
              <span class="link-token">{{ link.token.slice(0, 8) }}…</span>
              <span class="link-status" :class="statusClass(link)">{{ statusLabel(link) }}</span>
              <span class="link-expires">到期：{{ formatDate(link.expires_at) }}</span>
            </div>
            <div class="link-actions">
              <button
                v-if="!link.is_revoked && !link.is_expired"
                class="btn-copy"
                @click="copyLink(link.token)"
              >
                {{ copied === link.token ? '已複製！' : '複製連結' }}
              </button>
              <button
                v-if="!link.is_revoked"
                class="btn-revoke"
                @click="revoke(link.token)"
              >
                撤銷
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  albumId: { type: Number, required: true },
})
defineEmits(['close'])

const links = ref([])
const loading = ref(false)
const creating = ref(false)
const createError = ref('')
const expiresDays = ref(7)
const copied = ref(null)

async function loadLinks() {
  loading.value = true
  try {
    const { data } = await api.get(`/albums/${props.albumId}/share`)
    links.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function createLink() {
  creating.value = true
  createError.value = ''
  try {
    const { data } = await api.post(`/albums/${props.albumId}/share`, { expires_days: expiresDays.value })
    links.value.unshift(data)
  } catch (e) {
    createError.value = e.response?.data?.detail || '建立失敗'
  } finally {
    creating.value = false
  }
}

async function revoke(token) {
  if (!confirm('確定撤銷此連結？')) return
  try {
    await api.delete(`/share/${token}`)
    const link = links.value.find(l => l.token === token)
    if (link) link.is_revoked = true
  } catch (e) {
    alert('撤銷失敗：' + (e.response?.data?.detail || e.message))
  }
}

function copyLink(token) {
  const url = `${window.location.origin}/sites/photo-gallery/share/${token}`
  navigator.clipboard.writeText(url).then(() => {
    copied.value = token
    setTimeout(() => { copied.value = null }, 2000)
  })
}

function statusLabel(link) {
  if (link.is_revoked) return '已撤銷'
  if (link.is_expired) return '已過期'
  return '有效'
}

function statusClass(link) {
  if (link.is_revoked || link.is_expired) return 'inactive'
  return 'active'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(loadLinks)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}
.modal {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  width: 520px;
  max-width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.modal-header h2 {
  margin: 0;
  font-size: 17px;
  color: #e0e0e0;
}
.close-btn {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 18px;
}
.close-btn:hover { color: #ccc; }

.create-section {
  background: #252525;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}
.create-label {
  display: block;
  font-size: 13px;
  color: #aaa;
  margin-bottom: 10px;
}
.create-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.days-select {
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 13px;
}
.btn-primary {
  padding: 8px 16px;
  background: #5c6bc0;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.btn-primary:hover:not(:disabled) { background: #7986cb; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.error-msg {
  margin: 8px 0 0;
  font-size: 12px;
  color: #ef5350;
}

.links-section { }
.status-msg {
  text-align: center;
  color: #666;
  font-size: 13px;
  padding: 20px;
}
.links-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.link-item {
  background: #252525;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.link-item.inactive { opacity: 0.5; }
.link-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.link-token {
  font-family: monospace;
  font-size: 12px;
  color: #888;
}
.link-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.link-status.active { background: #1b5e20; color: #a5d6a7; }
.link-status.inactive { background: #333; color: #888; }
.link-expires {
  font-size: 12px;
  color: #666;
}
.link-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.btn-copy {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid #5c6bc0;
  color: #7986cb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.btn-copy:hover { background: rgba(92,107,192,0.15); }
.btn-revoke {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid #555;
  color: #888;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.btn-revoke:hover { border-color: #c62828; color: #ef5350; }
</style>
