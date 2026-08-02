import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    isAdmin: (state) => state.user?.is_admin ?? false,
  },

  actions: {
    async fetchMe() {
      const { data } = await api.get('/auth/me')
      this.user = data
    },
    async logout() {
      await api.post('/auth/logout')
      this.user = null
    },
  },
})
