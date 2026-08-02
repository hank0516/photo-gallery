<template>
  <div class="search-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.push('/')">← 相簿列表</button>
      <h1>搜尋照片</h1>
    </header>

    <div class="search-form">
      <input
        v-model="q"
        class="search-input"
        placeholder="搜尋檔名或說明…"
        @keydown.enter="doSearch"
      />
      <div class="filters">
        <label>
          <span>拍攝日期起</span>
          <input v-model="dateFrom" type="date" class="date-input" />
        </label>
        <label>
          <span>拍攝日期迄</span>
          <input v-model="dateTo" type="date" class="date-input" />
        </label>
        <label>
          <span>相簿</span>
          <select v-model="albumId" class="album-select">
            <option value="">全部</option>
            <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </label>
        <button class="btn-primary" :disabled="loading" @click="doSearch">
          {{ loading ? '搜尋中…' : '搜尋' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div v-if="searched" class="results-header">
      <ViewModeToggle v-model="viewMode" />
      <span class="result-count">共 {{ total }} 筆結果</span>
    </div>

    <div v-if="loading" class="loading">搜尋中…</div>

    <div v-else-if="searched && photos.length === 0" class="empty">
      找不到符合條件的照片
    </div>

    <template v-else-if="photos.length > 0">
      <PhotoGrid :photos="photos" :viewMode="viewMode" @open="openLightbox" />

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page === 1" @click="loadPage(page - 1)">‹ 上一頁</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page === totalPages" @click="loadPage(page + 1)">下一頁 ›</button>
      </div>
    </template>

    <Lightbox
      :visible="lightboxOpen"
      :photos="photos"
      :startIndex="lightboxIndex"
      myRole="viewer"
      @close="lightboxOpen = false"
      @update:startIndex="lightboxIndex = $event"
      @deleted="() => {}"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import PhotoGrid from '@/components/PhotoGrid.vue'
import Lightbox from '@/components/Lightbox.vue'
import ViewModeToggle from '@/components/ViewModeToggle.vue'

const route = useRoute()

const q = ref(route.query.q || '')
const dateFrom = ref('')
const dateTo = ref('')
const albumId = ref('')
const albums = ref([])

const photos = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 50
const loading = ref(false)
const error = ref(null)
const searched = ref(false)
const viewMode = ref(localStorage.getItem('viewMode') || 'small-grid')
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)

const totalPages = computed(() => Math.ceil(total.value / perPage))

async function loadAlbums() {
  try {
    const { data } = await api.get('/albums')
    albums.value = data
  } catch {}
}

async function doSearch() {
  await loadPage(1)
}

async function loadPage(p) {
  if (!q.value && !dateFrom.value && !dateTo.value && !albumId.value) {
    error.value = '請至少輸入一個搜尋條件'
    return
  }
  error.value = null
  loading.value = true
  try {
    const params = { page: p, per_page: perPage }
    if (q.value) params.q = q.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (albumId.value) params.album_id = albumId.value
    const { data } = await api.get('/search', { params })
    photos.value = data.photos
    total.value = data.total
    page.value = p
    searched.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || '搜尋失敗，請再試一次'
  } finally {
    loading.value = false
  }
}

function openLightbox(idx) {
  lightboxIndex.value = idx
  lightboxOpen.value = true
}

onMounted(async () => {
  await loadAlbums()
  if (q.value) doSearch()
})
</script>

<style scoped>
.search-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
  color: #e0e0e0;
}
.back-btn {
  background: transparent;
  border: 1px solid #333;
  color: #888;
  padding: 7px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.back-btn:hover { color: #ccc; border-color: #555; }

.search-form {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}
.search-input {
  width: 100%;
  padding: 10px 14px;
  background: #111;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 15px;
  margin-bottom: 12px;
  box-sizing: border-box;
}
.search-input:focus { outline: none; border-color: #5c6bc0; }
.search-input::placeholder { color: #555; }

.filters {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}
.filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #888;
}
.date-input, .album-select {
  padding: 7px 10px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 13px;
}
.date-input:focus, .album-select:focus { outline: none; border-color: #5c6bc0; }
.album-select { min-width: 140px; }

.btn-primary {
  padding: 8px 20px;
  background: #5c6bc0;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  align-self: flex-end;
}
.btn-primary:hover:not(:disabled) { background: #7986cb; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }

.error {
  color: #ef5350;
  font-size: 13px;
  margin: 8px 0 0;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.result-count {
  font-size: 13px;
  color: #666;
}

.loading, .empty {
  text-align: center;
  padding: 60px;
  color: #555;
  font-size: 14px;
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
