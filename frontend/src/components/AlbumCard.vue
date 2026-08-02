<template>
  <div class="album-card" @click="$router.push(`/albums/${album.id}`)">
    <div class="cover">
      <img v-if="album.cover_thumb_url" :src="album.cover_thumb_url" :alt="album.name" loading="lazy" />
      <div v-else class="cover-placeholder">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
      </div>
      <span class="role-badge" :class="album.my_role">{{ album.my_role }}</span>
    </div>
    <div class="info">
      <h3>{{ album.name }}</h3>
      <p class="desc">{{ album.description || ' ' }}</p>
      <div class="meta">
        <span v-if="album.album_date" class="album-date">{{ formatDate(album.album_date) }}</span>
        <span class="count">{{ album.photo_count }} 張</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  album: { type: Object, required: true },
})

function formatDate(d) {
  return d ? d.replace(/-/g, '.') : ''
}
</script>

<style scoped>
.album-card {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.album-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.cover {
  position: relative;
  aspect-ratio: 4/3;
  background: #2a2a2a;
  overflow: hidden;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #555;
}
.role-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}
.role-badge.admin { background: #5c6bc0; color: #fff; }
.role-badge.uploader { background: #388e3c; color: #fff; }
.role-badge.viewer { background: #455a64; color: #fff; }
.info {
  padding: 12px;
}
.info h3 {
  margin: 0 0 4px;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #e0e0e0;
}
.desc {
  margin: 0 0 6px;
  font-size: 12px;
  color: #888;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.album-date {
  font-size: 12px;
  color: #5c6bc0;
}
.count {
  font-size: 12px;
  color: #666;
}
</style>
