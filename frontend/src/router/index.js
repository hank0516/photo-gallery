import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/pages/LoginPage.vue'), meta: { public: true } },
  { path: '/share/:token', name: 'Shared', component: () => import('@/pages/SharedPage.vue'), meta: { public: true } },
  { path: '/', name: 'Albums', component: () => import('@/pages/AlbumsPage.vue') },
  { path: '/albums/:id', name: 'Album', component: () => import('@/pages/AlbumPage.vue') },
  { path: '/admin', name: 'Admin', component: () => import('@/pages/AdminPage.vue') },
  { path: '/search', name: 'Search', component: () => import('@/pages/SearchPage.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/pages/NotFoundPage.vue'), meta: { public: true } },
]

const router = createRouter({
  history: createWebHistory('/sites/photo-gallery/'),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (!auth.user) {
    await auth.fetchMe().catch(() => {})
  }

  if (!auth.isLoggedIn) {
    return { name: 'Login' }
  }
})

export default router
