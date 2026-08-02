<template>
  <div class="albums-page">
    <header class="page-header">
      <h1>相簿</h1>
      <div class="actions">
        <button class="btn-icon" :title="sortDesc ? '降冪（最新優先）' : '升冪（最舊優先）'" @click="toggleSort">
          {{ sortDesc ? '↓' : '↑' }}
        </button>
        <button
          v-if="hasLockedAlbums"
          class="btn-icon"
          :class="{ active: showLocked }"
          :title="showLocked ? '隱藏上鎖相簿' : '顯示上鎖相簿'"
          @click="showLocked = !showLocked"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="btn-icon" title="搜尋" @click="$router.push('/search')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>
        <button v-if="authStore.isAdmin" class="btn-primary" @click="showCreate = true">
          + 新增相簿
        </button>
        <RouterLink v-if="authStore.isAdmin" class="btn-icon" to="/admin" title="管理後台">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
            <circle cx="19" cy="8" r="2" />
            <line x1="19" y1="2" x2="19" y2="4" />
            <line x1="19" y1="12" x2="19" y2="14" />
            <line x1="15.5" y1="3.5" x2="17" y2="5" />
            <line x1="21" y1="11" x2="22.5" y2="12.5" />
            <line x1="22.5" y1="3.5" x2="21" y2="5" />
            <line x1="17" y1="11" x2="15.5" y2="12.5" />
          </svg>
        </RouterLink>
        <button class="btn-icon" title="登出" @click="authStore.logout()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
      </div>
    </header>

    <div v-if="albumsStore.loading" class="loading">載入中…</div>
    <div v-else-if="albumsStore.error" class="error">{{ albumsStore.error }}</div>
    <div v-else-if="albumsStore.albums.length === 0" class="empty">
      <p>尚無相簿。{{ authStore.isAdmin ? '建立第一個相簿吧！' : '請聯絡管理員取得相簿權限。' }}</p>
    </div>
    <template v-else>
      <section v-for="group in groupedAlbums" :key="group.year" class="year-section">
        <h2 class="year-header">{{ group.year }}</h2>
        <div class="albums-grid">
          <AlbumCard v-for="album in group.albums" :key="album.id" :album="album" />
        </div>
      </section>
    </template>

    <!-- Create Album Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="cancelCreate">
      <div class="modal">
        <h2>新增相簿</h2>
        <label>名稱 <span class="required">*</span></label>
        <input v-model="newName" placeholder="相簿名稱（含日期如 2025.03.15 可自動填入）" maxlength="100" autofocus @input="onNameInput" />
        <label>日期</label>
        <input
          v-model="newDate"
          type="date"
          :class="{ 'auto-filled': dateAutoFilled }"
          :title="dateAutoFilled ? '從名稱自動解析' : ''"
        />
        <label>描述</label>
        <input v-model="newDesc" placeholder="選填" maxlength="500" />
        <div class="lock-row">
          <label class="lock-label">
            <input type="checkbox" v-model="newLocked" />
            上鎖此相簿（需輸入密碼才能瀏覽）
          </label>
        </div>
        <template v-if="newLocked">
          <label>相簿密碼 <span class="required">*</span></label>
          <input v-model="newPassword" type="password" placeholder="設定密碼" autocomplete="new-password" />
        </template>
        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelCreate">取消</button>
          <button class="btn-primary" :disabled="!newName.trim() || (newLocked && !newPassword) || creating" @click="handleCreate">
            {{ creating ? '建立中…' : '建立' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAlbumsStore } from '@/stores/albums'
import { useAuthStore } from '@/stores/auth'
import AlbumCard from '@/components/AlbumCard.vue'

const albumsStore = useAlbumsStore()
const authStore = useAuthStore()

const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')
const newDate = ref('')
const newLocked = ref(false)
const newPassword = ref('')
const dateAutoFilled = ref(false)
const creating = ref(false)

const sortDesc = ref(localStorage.getItem('pg_album_sort') !== 'asc')
const showLocked = ref(false)

const hasLockedAlbums = computed(() => albumsStore.albums.some(a => a.is_locked))

const DATE_RE = /(\d{4})[.\-](\d{2})[.\-](\d{2})/

function parseDateFromName(name) {
  const m = name.match(DATE_RE)
  if (!m) return ''
  return `${m[1]}-${m[2]}-${m[3]}`
}

function onNameInput() {
  const parsed = parseDateFromName(newName.value)
  if (parsed) {
    newDate.value = parsed
    dateAutoFilled.value = true
  } else if (dateAutoFilled.value) {
    newDate.value = ''
    dateAutoFilled.value = false
  }
}

watch(newDate, () => {
  if (!parseDateFromName(newName.value)) dateAutoFilled.value = false
})

function toggleSort() {
  sortDesc.value = !sortDesc.value
  localStorage.setItem('pg_album_sort', sortDesc.value ? 'desc' : 'asc')
}

const groupedAlbums = computed(() => {
  const albums = albumsStore.albums.filter(a => showLocked.value || !a.is_locked)
  const dated = albums.filter(a => a.album_date)
  const undated = albums.filter(a => !a.album_date)

  dated.sort((a, b) => {
    const diff = a.album_date < b.album_date ? -1 : a.album_date > b.album_date ? 1 : 0
    return sortDesc.value ? -diff : diff
  })

  const byYear = {}
  for (const album of dated) {
    const year = album.album_date.slice(0, 4)
    if (!byYear[year]) byYear[year] = []
    byYear[year].push(album)
  }

  const years = Object.keys(byYear).sort((a, b) => sortDesc.value ? b - a : a - b)
  const groups = years.map(y => ({ year: y, albums: byYear[y] }))

  if (undated.length > 0) {
    groups.push({ year: '未分類', albums: undated })
  }

  return groups
})

function cancelCreate() {
  showCreate.value = false
  newName.value = ''
  newDesc.value = ''
  newDate.value = ''
  newLocked.value = false
  newPassword.value = ''
  dateAutoFilled.value = false
}

async function handleCreate() {
  if (!newName.value.trim()) return
  if (newLocked.value && !newPassword.value) return
  creating.value = true
  try {
    await albumsStore.createAlbum(
      newName.value.trim(),
      newDesc.value.trim(),
      newDate.value || null,
      newLocked.value ? newPassword.value : null,
    )
    cancelCreate()
  } finally {
    creating.value = false
  }
}

onMounted(() => albumsStore.fetchAlbums())
</script>

<style scoped>
.albums-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
}
.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #e0e0e0;
}
.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.btn-primary {
  padding: 8px 18px;
  background: #5c6bc0;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.btn-primary:hover:not(:disabled) { background: #7986cb; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-secondary {
  padding: 8px 18px;
  background: #333;
  color: #ccc;
  border: 1px solid #444;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.btn-secondary:hover { background: #404040; }
.btn-icon {
  background: transparent;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 7px 10px;
  cursor: pointer;
  color: #888;
  display: flex;
  align-items: center;
  font-size: 14px;
}
.btn-icon:hover { color: #ccc; border-color: #555; }
.btn-icon.active { color: #ffcc80; border-color: #ffcc80; }

.year-section { margin-bottom: 32px; }
.year-header {
  margin: 0 0 14px;
  font-size: 18px;
  font-weight: 600;
  color: #aaa;
  border-bottom: 1px solid #2a2a2a;
  padding-bottom: 6px;
}
.albums-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}
.loading, .empty {
  text-align: center;
  padding: 60px 0;
  color: #666;
}
.error {
  text-align: center;
  padding: 40px;
  color: #ef5350;
}
/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 28px;
  width: 400px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.modal h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #e0e0e0;
}
.modal label {
  font-size: 13px;
  color: #aaa;
}
.required { color: #ef5350; }
.modal input {
  width: 100%;
  padding: 9px 12px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 14px;
  box-sizing: border-box;
}
.modal input:focus {
  outline: none;
  border-color: #5c6bc0;
}
.modal input.auto-filled {
  border-color: #388e3c;
  color: #81c784;
}
.lock-row { display: flex; align-items: center; }
.lock-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #ccc; cursor: pointer; }
.lock-label input[type="checkbox"] { width: 15px; height: 15px; cursor: pointer; }
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
