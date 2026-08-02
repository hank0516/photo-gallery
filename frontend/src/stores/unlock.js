import { defineStore } from 'pinia'

// Session-only: tokens are lost on page reload (by design)
export const useUnlockStore = defineStore('unlock', {
  state: () => ({ tokens: {} }),  // { [albumId]: unlock_token }

  getters: {
    isUnlocked: (state) => (albumId) => !!state.tokens[albumId],
    getToken: (state) => (albumId) => state.tokens[albumId] ?? null,
  },

  actions: {
    setToken(albumId, token) {
      this.tokens[albumId] = token
    },
    clear(albumId) {
      delete this.tokens[albumId]
    },
  },
})
