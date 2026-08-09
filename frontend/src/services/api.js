import axios from 'axios'
import router from '@/router'

const api = axios.create({
  baseURL: '/api/photo-gallery',
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !router.currentRoute.value.meta.public) {
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default api
