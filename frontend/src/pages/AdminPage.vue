<template>
  <div class="admin-page">
    <header class="page-header">
      <RouterLink to="/" class="back-link">← 相簿</RouterLink>
      <h1>管理後台</h1>
    </header>

    <div class="tabs">
      <button
        v-for="t in TABS" :key="t.key"
        :class="['tab-btn', { active: tab === t.key }]"
        @click="switchTab(t.key)"
      >{{ t.label }}</button>
    </div>

    <!-- ── Users ── -->
    <section v-if="tab === 'users'" class="tab-content">
      <div v-if="usersLoading" class="loading">載入中…</div>
      <div v-else-if="usersError" class="error">{{ usersError }}</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>名稱</th>
            <th>Email</th>
            <th>角色</th>
            <th>加入時間</th>
            <th>上次登入</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="name-cell">
              <img v-if="u.avatar_url" :src="u.avatar_url" class="avatar" referrerpolicy="no-referrer" />
              <span>{{ u.name }}</span>
            </td>
            <td>{{ u.email }}</td>
            <td>
              <span :class="u.is_admin ? 'badge-admin' : 'badge-user'">
                {{ u.is_admin ? 'Admin' : 'User' }}
              </span>
            </td>
            <td class="mono time-cell">{{ fmtDate(u.created_at) }}</td>
            <td class="mono time-cell">{{ fmtDate(u.last_login_at) }}</td>
            <td class="actions-cell">
              <button
                class="btn-sm"
                :disabled="u.id === authStore.user?.id"
                :title="u.id === authStore.user?.id ? '無法修改自己' : ''"
                @click="toggleAdmin(u)"
              >{{ u.is_admin ? '取消管理員' : '設為管理員' }}</button>
              <button class="btn-sm btn-accent" @click="openPerms(u)">相簿權限</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── Login Logs ── -->
    <section v-if="tab === 'login-logs'" class="tab-content">
      <div class="filter-bar">
        <input v-model="loginFilter.email" placeholder="Email 篩選" @keyup.enter="fetchLoginLogs(1)" />
        <button class="btn-sm btn-accent" @click="fetchLoginLogs(1)">搜尋</button>
      </div>
      <div v-if="loginLoading" class="loading">載入中…</div>
      <template v-else>
        <table class="data-table">
          <thead>
            <tr><th>時間</th><th>Email</th><th>IP</th><th>User Agent</th></tr>
          </thead>
          <tbody>
            <tr v-for="l in loginLogs.items" :key="l.id">
              <td class="mono time-cell">{{ fmtDateTime(l.logged_in_at) }}</td>
              <td>{{ l.email }}</td>
              <td class="mono">{{ l.ip_address || '-' }}</td>
              <td class="ua-cell" :title="l.user_agent">{{ l.user_agent || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="pagination">
          <button :disabled="loginLogs.page <= 1" @click="fetchLoginLogs(loginLogs.page - 1)">‹ 上一頁</button>
          <span>第 {{ loginLogs.page }} 頁 ／ 共 {{ loginLogs.total }} 筆</span>
          <button :disabled="loginLogs.page * loginLogs.per_page >= loginLogs.total" @click="fetchLoginLogs(loginLogs.page + 1)">下一頁 ›</button>
        </div>
      </template>
    </section>

    <!-- ── Request Logs ── -->
    <section v-if="tab === 'request-logs'" class="tab-content">
      <div class="filter-bar">
        <input v-model="reqFilter.email" placeholder="Email" @keyup.enter="fetchRequestLogs(1)" />
        <input v-model="reqFilter.path" placeholder="Path" @keyup.enter="fetchRequestLogs(1)" />
        <select v-model="reqFilter.method" class="method-select">
          <option value="">全部</option>
          <option>GET</option><option>POST</option>
          <option>PUT</option><option>PATCH</option><option>DELETE</option>
        </select>
        <button class="btn-sm btn-accent" @click="fetchRequestLogs(1)">搜尋</button>
      </div>
      <div v-if="reqLoading" class="loading">載入中…</div>
      <template v-else>
        <table class="data-table">
          <thead>
            <tr><th>時間</th><th>Email</th><th>方法</th><th>Path</th><th>狀態</th><th>回應 ms</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in requestLogs.items" :key="r.id">
              <td class="mono time-cell">{{ fmtDateTime(r.requested_at) }}</td>
              <td>{{ r.email || '-' }}</td>
              <td><span :class="'method method-' + r.method">{{ r.method }}</span></td>
              <td class="path-cell" :title="r.path">{{ r.path }}</td>
              <td><span :class="statusClass(r.status_code)">{{ r.status_code }}</span></td>
              <td class="mono">{{ r.response_time_ms ?? '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="pagination">
          <button :disabled="requestLogs.page <= 1" @click="fetchRequestLogs(requestLogs.page - 1)">‹ 上一頁</button>
          <span>第 {{ requestLogs.page }} 頁 ／ 共 {{ requestLogs.total }} 筆</span>
          <button :disabled="requestLogs.page * requestLogs.per_page >= requestLogs.total" @click="fetchRequestLogs(requestLogs.page + 1)">下一頁 ›</button>
        </div>
      </template>
    </section>

    <!-- ── Permission Modal ── -->
    <div v-if="permUser" class="modal-overlay" @click.self="permUser = null">
      <div class="perm-modal">
        <div class="modal-header">
          <div>
            <div class="perm-name">{{ permUser.name }}</div>
            <div class="perm-email">{{ permUser.email }}</div>
          </div>
          <button class="close-btn" @click="permUser = null">✕</button>
        </div>
        <div v-if="permLoading" class="loading">載入中…</div>
        <div v-else-if="userPerms.length === 0" class="empty">目前沒有相簿</div>
        <div v-else class="perm-list">
          <div v-for="a in userPerms" :key="a.album_id" class="perm-row">
            <span class="perm-album">{{ a.album_name }}</span>
            <select :value="a.role ?? ''" class="role-select" @change="onRoleChange(a, $event.target.value)">
              <option value="">無存取</option>
              <option value="viewer">Viewer</option>
              <option value="uploader">Uploader</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const TABS = [
  { key: 'users', label: '使用者' },
  { key: 'login-logs', label: '登入紀錄' },
  { key: 'request-logs', label: '請求紀錄' },
]

const tab = ref('users')

// ── Users ──
const users = ref([])
const usersLoading = ref(false)
const usersError = ref('')

async function fetchUsers() {
  usersLoading.value = true
  usersError.value = ''
  try {
    const { data } = await api.get('/admin/users')
    users.value = data
  } catch (e) {
    usersError.value = e.response?.data?.detail || '載入失敗'
  } finally {
    usersLoading.value = false
  }
}

async function toggleAdmin(user) {
  try {
    const { data } = await api.patch(`/admin/users/${user.id}`, { is_admin: !user.is_admin })
    user.is_admin = data.is_admin
  } catch (e) {
    alert('操作失敗：' + (e.response?.data?.detail || e.message))
  }
}

// ── Permissions Modal ──
const permUser = ref(null)
const userPerms = ref([])
const permLoading = ref(false)

async function openPerms(user) {
  permUser.value = user
  permLoading.value = true
  userPerms.value = []
  try {
    const { data } = await api.get(`/admin/users/${user.id}/permissions`)
    userPerms.value = data
  } finally {
    permLoading.value = false
  }
}

async function onRoleChange(album, newRole) {
  const userId = permUser.value.id
  try {
    if (!newRole) {
      await api.delete(`/albums/${album.album_id}/permissions/${userId}`)
    } else {
      await api.put(`/albums/${album.album_id}/permissions/${userId}`, { role: newRole })
    }
    album.role = newRole || null
  } catch (e) {
    alert('操作失敗：' + (e.response?.data?.detail || e.message))
  }
}

// ── Login Logs ──
const loginLoading = ref(false)
const loginFilter = reactive({ email: '' })
const loginLogs = reactive({ items: [], total: 0, page: 1, per_page: 50 })

async function fetchLoginLogs(page = 1) {
  loginLoading.value = true
  try {
    const { data } = await api.get('/admin/login-logs', {
      params: { page, per_page: 50, email: loginFilter.email },
    })
    Object.assign(loginLogs, data)
  } finally {
    loginLoading.value = false
  }
}

// ── Request Logs ──
const reqLoading = ref(false)
const reqFilter = reactive({ email: '', path: '', method: '' })
const requestLogs = reactive({ items: [], total: 0, page: 1, per_page: 50 })

async function fetchRequestLogs(page = 1) {
  reqLoading.value = true
  try {
    const { data } = await api.get('/admin/request-logs', {
      params: { page, per_page: 50, ...reqFilter },
    })
    Object.assign(requestLogs, data)
  } finally {
    reqLoading.value = false
  }
}

function switchTab(key) {
  tab.value = key
  if (key === 'users' && users.value.length === 0) fetchUsers()
  if (key === 'login-logs' && loginLogs.items.length === 0) fetchLoginLogs(1)
  if (key === 'request-logs' && requestLogs.items.length === 0) fetchRequestLogs(1)
}

// ── Formatters ──
function fmtDate(iso) {
  if (!iso) return '-'
  return iso.slice(0, 10)
}

function fmtDateTime(iso) {
  if (!iso) return '-'
  return iso.replace('T', ' ').slice(0, 19)
}

function statusClass(code) {
  if (code < 300) return 'status status-2xx'
  if (code < 400) return 'status status-3xx'
  if (code < 500) return 'status status-4xx'
  return 'status status-5xx'
}

onMounted(async () => {
  if (!authStore.user) await authStore.fetchMe().catch(() => {})
  if (!authStore.isAdmin) { router.replace('/'); return }
  fetchUsers()
})
</script>

<style scoped>
.admin-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header h1 { margin: 0; font-size: 22px; color: #e0e0e0; }
.back-link { color: #888; text-decoration: none; font-size: 14px; white-space: nowrap; }
.back-link:hover { color: #ccc; }

/* Tabs */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 1px solid #2a2a2a; }
.tab-btn {
  padding: 8px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #888;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: -1px;
}
.tab-btn:hover { color: #ccc; }
.tab-btn.active { color: #7986cb; border-bottom-color: #7986cb; }

/* Table */
.tab-content { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  text-align: left;
  padding: 8px 12px;
  color: #777;
  font-weight: 500;
  border-bottom: 1px solid #2a2a2a;
  white-space: nowrap;
}
.data-table td { padding: 9px 12px; border-bottom: 1px solid #1e1e1e; vertical-align: middle; }
.data-table tbody tr:hover { background: #1a1a1a; }

.name-cell { display: flex; align-items: center; gap: 8px; }
.avatar { width: 26px; height: 26px; border-radius: 50%; object-fit: cover; }
.mono { font-family: 'Menlo', 'Consolas', monospace; font-size: 12px; }
.time-cell { color: #888; white-space: nowrap; }
.ua-cell { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #777; }
.path-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace; font-size: 12px; }
.actions-cell { display: flex; gap: 6px; align-items: center; white-space: nowrap; }

/* Badges */
.badge-admin { background: #3949ab; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.badge-user  { background: #333; color: #aaa; padding: 2px 8px; border-radius: 10px; font-size: 11px; }

/* Method badges */
.method { padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; font-family: monospace; }
.method-GET    { background: #2e2e2e; color: #9e9e9e; }
.method-POST   { background: #1b3a1b; color: #66bb6a; }
.method-PUT    { background: #0d2b45; color: #42a5f5; }
.method-PATCH  { background: #3a2800; color: #ffa726; }
.method-DELETE { background: #3b1111; color: #ef5350; }

/* Status badges */
.status { padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; font-family: monospace; }
.status-2xx { background: #1b3a1b; color: #66bb6a; }
.status-3xx { background: #0d2b45; color: #42a5f5; }
.status-4xx { background: #3a2800; color: #ffa726; }
.status-5xx { background: #3b1111; color: #ef5350; }

/* Buttons */
.btn-sm {
  padding: 5px 12px;
  font-size: 12px;
  border: 1px solid #444;
  border-radius: 5px;
  background: #2a2a2a;
  color: #ccc;
  cursor: pointer;
}
.btn-sm:hover:not(:disabled) { background: #333; color: #e0e0e0; }
.btn-sm:disabled { opacity: 0.35; cursor: default; }
.btn-accent { background: #283593; border-color: #3949ab; color: #c5cae9; }
.btn-accent:hover:not(:disabled) { background: #303f9f; }

/* Filters */
.filter-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.filter-bar input {
  padding: 6px 10px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 5px;
  color: #e0e0e0;
  font-size: 13px;
  width: 200px;
}
.filter-bar input:focus { outline: none; border-color: #5c6bc0; }
.method-select {
  padding: 6px 10px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 5px;
  color: #e0e0e0;
  font-size: 13px;
}

/* Pagination */
.pagination { display: flex; align-items: center; gap: 14px; margin-top: 14px; color: #888; font-size: 13px; }
.pagination button {
  padding: 5px 12px;
  background: #222;
  border: 1px solid #333;
  border-radius: 5px;
  color: #ccc;
  cursor: pointer;
  font-size: 13px;
}
.pagination button:hover:not(:disabled) { background: #2a2a2a; }
.pagination button:disabled { opacity: 0.3; cursor: default; }

/* Permission Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.perm-modal {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 10px;
  width: 480px;
  max-width: 95vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 20px 14px;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.perm-name { font-size: 16px; font-weight: 600; color: #e0e0e0; }
.perm-email { font-size: 12px; color: #888; margin-top: 2px; }
.close-btn { background: none; border: none; color: #666; font-size: 18px; cursor: pointer; padding: 0 0 0 16px; }
.close-btn:hover { color: #ccc; }

.perm-list { overflow-y: auto; padding: 8px 0; }
.perm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 20px;
  gap: 12px;
}
.perm-row:hover { background: #252525; }
.perm-album { font-size: 13px; color: #ccc; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.role-select {
  padding: 4px 8px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 5px;
  color: #e0e0e0;
  font-size: 12px;
  flex-shrink: 0;
}

.loading { padding: 40px; text-align: center; color: #666; }
.empty   { padding: 24px 20px; text-align: center; color: #555; font-size: 13px; }
.error   { padding: 20px; text-align: center; color: #ef5350; }
</style>
