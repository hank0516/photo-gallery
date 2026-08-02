<template>
  <div class="album-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.push('/')">← 相簿列表</button>
      <div class="header-center">
        <h1 v-if="albumData">{{ albumData.album.name }}</h1>
      </div>
      <div class="header-right">
        <ViewModeToggle v-model="viewMode" />
        <button v-if="isAdmin" class="btn-secondary" @click="showMembers = true">
          管理成員
        </button>
        <button v-if="canUpload" class="btn-primary" @click="showUpload = true">
          上傳照片
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">載入中…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else-if="albumData">
      <p v-if="albumData.album.description" class="album-desc">{{ albumData.album.description }}</p>
      <div class="album-stats">
        共 {{ albumData.total }} 張照片
        <span class="role-tag" :class="albumData.album.my_role">{{ albumData.album.my_role }}</span>
      </div>

      <PhotoGrid
        :photos="albumData.photos"
        :viewMode="viewMode"
        @open="openLightbox"
      />

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page === 1" @click="loadPage(page - 1)">‹ 上一頁</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page === totalPages" @click="loadPage(page + 1)">下一頁 ›</button>
      </div>
    </template>

    <Lightbox
      :visible="lightboxOpen"
      :photos="albumData?.photos ?? []"
      :startIndex="lightboxIndex"
      :myRole="albumData?.album?.my_role ?? ''"
      @close="lightboxOpen = false"
      @update:startIndex="lightboxIndex = $event"
      @deleted="onPhotoDeleted"
    />

    <!-- Members Modal -->
    <MembersModal
      v-if="showMembers"
      :albumId="albumId"
      :albumName="albumData?.album.name ?? ''"
      @close="showMembers = false"
    />

    <!-- Upload Modal -->
    <div v-if="showUpload" class="modal-overlay" @click.self="showUpload = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>上傳照片到「{{ albumData?.album.name }}」</h2>
          <button class="close-btn" @click="showUpload = false">✕</button>
        </div>
        <UploadZone :albumId="albumId" @uploaded="onPhotoUploaded" />
        <p class="upload-note">上傳完成後，重新整理頁面可看到新照片。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import ViewModeToggle from '@/components/ViewModeToggle.vue'
import PhotoGrid from '@/components/PhotoGrid.vue'
import Lightbox from '@/components/Lightbox.vue'
import UploadZone from '@/components/UploadZone.vue'
import MembersModal from '@/components/MembersModal.vue'

const route = useRoute()
const albumId = computed(() => Number(route.params.id))

const albumData = ref(null)
const loading = ref(false)
const error = ref(null)
const page = ref(1)
const perPage = 100
const viewMode = ref(localStorage.getItem('viewMode') || 'small-grid')
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const showUpload = ref(false)
const showMembers = ref(false)

const totalPages = computed(() => Math.ceil((albumData.value?.total ?? 0) / perPage))
const canUpload = computed(() => ['admin', 'uploader'].includes(albumData.value?.album?.my_role))
const isAdmin = computed(() => albumData.value?.album?.my_role === 'admin')

async function loadPage(p) {
  loading.value = true
  error.value = null
  try {
    const { data } = await api.get(`/albums/${albumId.value}`, {
      params: { page: p, per_page: perPage },
    })
    albumData.value = data
    page.value = p
  } catch (e) {
    error.value = e.response?.data?.detail || '無法載入相簿'
  } finally {
    loading.value = false
  }
}

function openLightbox(idx) {
  lightboxIndex.value = idx
  lightboxOpen.value = true
}

function onPhotoUploaded(newPhoto) {
  if (albumData.value) {
    albumData.value.photos.unshift(newPhoto)
    albumData.value.total += 1
  }
}

function onPhotoDeleted(photoId) {
  if (albumData.value) {
    albumData.value.photos = albumData.value.photos.filter(p => p.id !== photoId)
    albumData.value.total -= 1
  }
}

watch(viewMode, v => localStorage.setItem('viewMode', v))
onMounted(() => loadPage(1))
</script>

<style scoped>
.album-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
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
  flex-shrink: 0;
}
.back-btn:hover { color: #ccc; border-color: #555; }
.header-center { flex: 1; min-width: 0; }
.header-center h1 {
  margin: 0;
  font-size: 20px;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.btn-primary {
  padding: 8px 16px;
  background: #5c6bc0;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.btn-primary:hover { background: #7986cb; }
.btn-secondary {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #444;
  color: #aaa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.btn-secondary:hover { border-color: #666; color: #ccc; }
.album-desc {
  color: #888;
  font-size: 14px;
  margin: 0 0 12px;
}
.album-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #666;
}
.role-tag {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}
.role-tag.admin { background: #5c6bc0; color: #fff; }
.role-tag.uploader { background: #388e3c; color: #fff; }
.role-tag.viewer { background: #455a64; color: #fff; }
.loading, .error {
  text-align: center;
  padding: 60px;
  color: #666;
}
.error { color: #ef5350; }
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
/* Upload Modal */
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
  width: 560px;
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
.upload-note {
  margin: 16px 0 0;
  font-size: 12px;
  color: #555;
  text-align: center;
}
</style>
