<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>管理成員 — {{ albumName }}</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Current members -->
      <div class="section-label">目前成員</div>
      <div v-if="loadingPerms" class="loading">載入中…</div>
      <div v-else-if="perms.length === 0" class="empty">尚無成員</div>
      <div v-else class="members-list">
        <div v-for="p in perms" :key="p.user_id" class="member-row">
          <div class="member-info">
            <span class="member-name">{{ p.name }}</span>
            <span class="member-email">{{ p.email }}</span>
          </div>
          <select :value="p.role" @change="changeRole(p.user_id, $event.target.value)" class="role-select">
            <option value="viewer">viewer</option>
            <option value="uploader">uploader</option>
            <option value="admin">admin</option>
          </select>
          <button class="remove-btn" @click="removeMember(p.user_id)" title="移除">✕</button>
        </div>
      </div>

      <!-- Add member -->
      <div class="section-label" style="margin-top:20px">新增成員</div>
      <div v-if="loadingUsers" class="loading">載入中…</div>
      <div v-else class="add-row">
        <select v-model="selectedUserId" class="user-select">
          <option value="">選擇使用者…</option>
          <option
            v-for="u in availableUsers"
            :key="u.id"
            :value="u.id"
          >{{ u.name }} ({{ u.email }})</option>
        </select>
        <select v-model="selectedRole" class="role-select">
          <option value="viewer">viewer</option>
          <option value="uploader">uploader</option>
          <option value="admin">admin</option>
        </select>
        <button
          class="btn-primary"
          :disabled="!selectedUserId || adding"
          @click="addMember"
        >{{ adding ? '…' : '新增' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  albumId: { type: Number, required: true },
  albumName: { type: String, default: '' },
})
defineEmits(['close'])

const perms = ref([])
const allUsers = ref([])
const loadingPerms = ref(false)
const loadingUsers = ref(false)
const selectedUserId = ref('')
const selectedRole = ref('viewer')
const adding = ref(false)

const availableUsers = computed(() => {
  const existingIds = new Set(perms.value.map(p => p.user_id))
  return allUsers.value.filter(u => !existingIds.has(u.id))
})

async function loadPerms() {
  loadingPerms.value = true
  try {
    const { data } = await api.get(`/albums/${props.albumId}/permissions`)
    perms.value = data
  } finally {
    loadingPerms.value = false
  }
}

async function loadUsers() {
  loadingUsers.value = true
  try {
    const { data } = await api.get('/users')
    allUsers.value = data
  } finally {
    loadingUsers.value = false
  }
}

async function addMember() {
  if (!selectedUserId.value) return
  adding.value = true
  try {
    await api.put(`/albums/${props.albumId}/permissions/${selectedUserId.value}`, {
      role: selectedRole.value,
    })
    await loadPerms()
    selectedUserId.value = ''
    selectedRole.value = 'viewer'
  } finally {
    adding.value = false
  }
}

async function changeRole(userId, newRole) {
  await api.put(`/albums/${props.albumId}/permissions/${userId}`, { role: newRole })
  const p = perms.value.find(p => p.user_id === userId)
  if (p) p.role = newRole
}

async function removeMember(userId) {
  if (!confirm('確定要移除此成員？')) return
  await api.delete(`/albums/${props.albumId}/permissions/${userId}`)
  perms.value = perms.value.filter(p => p.user_id !== userId)
}

onMounted(() => {
  loadPerms()
  loadUsers()
})
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
  max-height: 85vh;
  overflow-y: auto;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.modal-header h2 { margin: 0; font-size: 17px; color: #e0e0e0; }
.close-btn {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 18px;
}
.close-btn:hover { color: #ccc; }
.section-label {
  font-size: 11px;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}
.loading, .empty { font-size: 13px; color: #555; padding: 8px 0; }
.members-list { display: flex; flex-direction: column; gap: 6px; }
.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #2a2a2a;
  border-radius: 6px;
  padding: 8px 12px;
}
.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.member-name { font-size: 13px; color: #ddd; }
.member-email { font-size: 11px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.role-select {
  background: #333;
  border: 1px solid #444;
  border-radius: 4px;
  color: #ccc;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}
.remove-btn {
  background: transparent;
  border: none;
  color: #555;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  flex-shrink: 0;
}
.remove-btn:hover { color: #ef5350; }
.add-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.user-select {
  flex: 1;
  min-width: 160px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #ccc;
  padding: 8px 10px;
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
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-primary:hover:not(:disabled) { background: #7986cb; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
</style>
