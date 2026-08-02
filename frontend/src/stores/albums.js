import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAlbumsStore = defineStore('albums', () => {
  const albums = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchAlbums() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/albums')
      albums.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load albums'
    } finally {
      loading.value = false
    }
  }

  async function createAlbum(name, description, album_date) {
    const { data } = await api.post('/albums', { name, description, album_date })
    albums.value.unshift(data)
    return data
  }

  async function updateAlbum(albumId, patch) {
    const { data } = await api.patch(`/albums/${albumId}`, patch)
    const idx = albums.value.findIndex(a => a.id === albumId)
    if (idx !== -1) albums.value[idx] = data
    return data
  }

  async function deleteAlbum(albumId) {
    await api.delete(`/albums/${albumId}`)
    albums.value = albums.value.filter(a => a.id !== albumId)
  }

  return { albums, loading, error, fetchAlbums, createAlbum, updateAlbum, deleteAlbum }
})
