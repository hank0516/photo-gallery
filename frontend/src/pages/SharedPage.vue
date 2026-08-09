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

const totalPages = computed(() => Math.ceil((data.value?.total ?? 0) / perPage))

const publicApi = axios.create({ baseURL: '/api/photo-gallery' })

async function loadPage(p) {
  loading.value = true
  error.value = null
  try {
    const { data: res } = await publicApi.get(`/share/${token}`, { params: { page: p, per_page: perPage } })
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
</style>
