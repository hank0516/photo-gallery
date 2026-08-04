<template>
  <div :class="['photo-grid', `mode-${viewMode}`]">
    <template v-if="viewMode !== 'list'">
      <div
        v-for="(photo, idx) in photos"
        :key="photo.id"
        class="grid-item"
        @click="$emit('open', idx)"
      >
        <img
          v-if="photo.thumb_300_url"
          :src="photo.thumb_300_url"
          :alt="photo.caption || photo.filename"
          loading="lazy"
        />
        <div v-else class="thumb-placeholder">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>
        </div>
        <div v-if="isVideo(photo)" class="play-overlay">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        </div>
        <div class="overlay">
          <span v-if="photo.caption" class="caption">{{ photo.caption }}</span>
        </div>
      </div>
    </template>

    <template v-else>
      <div
        v-for="(photo, idx) in photos"
        :key="photo.id"
        class="list-item"
        @click="$emit('open', idx)"
      >
        <div class="list-thumb-wrap">
          <img
            v-if="photo.thumb_300_url"
            :src="photo.thumb_300_url"
            :alt="photo.filename"
            loading="lazy"
            class="list-thumb"
          />
          <div v-else class="list-thumb thumb-placeholder">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>
          </div>
          <div v-if="isVideo(photo)" class="list-play-badge">▶</div>
        </div>
        <div class="list-info">
          <span class="list-filename">{{ photo.filename }}</span>
          <span v-if="photo.caption" class="list-caption">{{ photo.caption }}</span>
          <span class="list-meta">
            <template v-if="photo.exif_date_taken">{{ formatDate(photo.exif_date_taken) }}</template>
            <template v-if="photo.width">{{ photo.width }} × {{ photo.height }}</template>
          </span>
        </div>
      </div>
    </template>

    <div v-if="photos.length === 0" class="empty">此相簿還沒有照片或影片</div>
  </div>
</template>

<script setup>
defineProps({
  photos: { type: Array, default: () => [] },
  viewMode: { type: String, default: 'small-grid' },
})
defineEmits(['open'])

function isVideo(photo) {
  return photo.mime_type?.startsWith('video/')
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
/* Small grid — 4+ columns (3 on mobile) */
.mode-small-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 3px;
}

/* Large grid — 2-3 columns (2 on mobile) */
.mode-large-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 4px;
}

.grid-item {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  cursor: pointer;
  background: #1e1e1e;
}
.grid-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}
.grid-item:hover img { transform: scale(1.04); }

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1e1e1e;
  color: #444;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.play-overlay svg {
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.8));
  opacity: 0.9;
  color: #fff;
}

.overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  opacity: 0;
  transition: opacity 0.2s;
}
.grid-item:hover .overlay { opacity: 1; }
.caption {
  font-size: 12px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

/* List */
.mode-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.list-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 12px;
  background: #1e1e1e;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.1s;
}
.list-item:hover { background: #2a2a2a; }
.list-thumb-wrap {
  position: relative;
  flex-shrink: 0;
  width: 56px;
  height: 56px;
}
.list-thumb {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}
.list-thumb-wrap .thumb-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  color: #444;
}
.list-play-badge {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: rgba(255,255,255,0.85);
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
  pointer-events: none;
}
.list-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
}
.list-filename {
  font-size: 14px;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.list-caption {
  font-size: 12px;
  color: #888;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.list-meta {
  font-size: 11px;
  color: #555;
  display: flex;
  gap: 12px;
}
.empty {
  text-align: center;
  padding: 60px;
  color: #555;
}
</style>
