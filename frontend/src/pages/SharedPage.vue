<template>
  <div class="shared-page">
    <!-- Loading -->
    <div v-if="loading" class="status-center">載入中…</div>

    <!-- Error -->
    <div v-else-if="error" class="status-center error-block">
      <div class="error-icon">🔗</div>
      <h2>{{ error }}</h2>
      <p class="error-sub">請確認連結是否正確，或聯繫相簿擁有者</p>
    </div>

    <!-- Lock gate -->
    <div v-else-if="isLocked" class="status-center">
      <div class="lock-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
      </div>
      <h2 class="lock-title">{{ data.album.name }}</h2>
      <p class="lock-desc">{{ data.album.description || '此相簿已上鎖，請輸入密碼' }}</p>
      <form class="lock-form" @submit.prevent="handleUnlock">
        <input
          v-model="passwordInput"
          type="password"
          placeholder="輸入密碼"
          class="lock-input"
          autofocus
          :disabled="unlocking"
        />
        <button type="submit" class="btn-primary lock-btn" :disabled="!passwordInput || unlocking">
          {{ unlocking ? '驗證中…' : '解鎖' }}
        </button>
      </form>
      <p v-if="lockError" class="lock-error">{{ lockError }}</p>
    </div>

    <!-- Content -->
    <template v-else-if="data">
      <header class="page-header">
        <div class="album-title">
          <h1>{{ data.album.name }}</h1>
          <p v-if="data.album.description" class="album-desc">{{ data.album.description }}</p>
        </div>
        <div class="header-meta">
          <span class="photo-count">{{ data.total }} 張照片</span>
          <span class="expires-info">連結到期：{{ formatDate(data.expires_at) }}</span>
        </div>
      </header>

      <ViewModeToggle v-model="viewMode" />

      <PhotoGrid
        :photos="data.photos"
        :viewMode="viewMode"
        @open="openLightbox"
      />

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page === 1" @click="loadPage(page - 1)">‹ 上一頁</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page === totalPages" @click="loadPage(page + 1)">下一頁 ›</button>
      </div>
    </template>

    <Lightbox
      :visible="lightboxOpen"
      :photos="data?.photos ?? []"
      :startIndex="lightboxIndex"
      myRole=""
      :showDownload="false"
      @close="lightboxOpen = false"
      @update:startIndex="lightboxIndex = $event"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import ViewModeToggle from '@/components/ViewModeToggle.vue'
import PhotoGrid from '@/components/PhotoGrid.vue'
import Lightbox from '@/components/Lightbox.vue'

const route = useRoute()
const token = route.params.token

const data = ref(null)
const loading = ref(false)
const error = ref(null)
const page = ref(1)
const perPage = 100
const viewMode = ref(localStorage.getItem('viewMode') || 'small-grid')
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const unlockToken = ref(null)
const passwordInput = ref('')
const unlocking = ref(false)
const lockError = ref('')

const totalPages = computed(() => Math.ceil((data.value?.total ?? 0) / perPage))
const isLocked = computed(() => data.value?.locked === true)

const publicApi = axios.create({ baseURL: '/api/photo-gallery' })

async function loadPage(p) {
  loading.value = true
  error.value = null
  try {
    const params = { page: p, per_page: perPage }
    if (unlockToken.value) params.unlock_token = unlockToken.value
    const { data: res } = await publicApi.get(`/share/${token}`, { params })
    data.value = res
    page.value = p
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 410) {
      error.value = detail || '此分享連結已過期或已被撤銷'
    } else if (status === 404) {
      error.value = detail || '找不到此分享連結'
    } else {
      error.value = '載入失敗，請稍後再試'
    }
  } finally {
    loading.value = false
  }
}

async function handleUnlock() {
  if (!passwordInput.value) return
  unlocking.value = true
  lockError.value = ''
  try {
    const { data: res } = await publicApi.post(`/share/${token}/unlock`, { password: passwordInput.value })
    unlockToken.value = res.unlock_token
    passwordInput.value = ''
    await loadPage(1)
  } catch (e) {
    lockError.value = e.response?.data?.detail || '驗證失敗'
  } finally {
    unlocking.value = false
  }
}

function openLightbox(idx) {
  lightboxIndex.value = idx
  lightboxOpen.value = true
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(() => loadPage(1))
</script>

<style scoped>
.shared-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px;
}
.status-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  color: #666;
  font-size: 15px;
}
.error-block { gap: 12px; }
.error-icon { font-size: 48px; opacity: 0.5; }
.error-block h2 {
  margin: 0;
  font-size: 20px;
  color: #e0e0e0;
}
.error-sub {
  margin: 0;
  font-size: 13px;
  color: #666;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.album-title h1 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #e0e0e0;
}
.album-desc {
  margin: 0;
  font-size: 13px;
  color: #888;
}
.header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}
.photo-count {
  font-size: 13px;
  color: #666;
}
.expires-info {
  font-size: 12px;
  color: #555;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  color: #888;
  font-size: 14px;
}
.pagination button {
  padding: 6px 16px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #ccc;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.3; cursor: default; }
.pagination button:hover:not(:disabled) { background: #333; }

/* Lock gate */
.lock-icon { color: #ffcc80; opacity: 0.8; margin-bottom: 8px; }
.lock-title { margin: 0 0 4px; font-size: 22px; color: #e0e0e0; }
.lock-desc { margin: 0 0 16px; font-size: 14px; color: #888; max-width: 300px; text-align: center; }
.lock-form { display: flex; gap: 8px; align-items: center; }
.lock-input {
  padding: 10px 14px;
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 14px;
  width: 220px;
}
.lock-input:focus { outline: none; border-color: #5c6bc0; }
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
.lock-btn { padding: 10px 20px; }
.lock-error { color: #ef5350; font-size: 13px; margin: 8px 0 0; }
</style>
