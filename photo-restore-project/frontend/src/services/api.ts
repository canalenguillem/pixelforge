import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

/**
 * Instancia de Axios. baseURL = /api/v1 → el dev server de Vite lo proxya al
 * backend (backend:8000). El interceptor añade el Bearer token en cada petición.
 */
export const api = axios.create({
  baseURL: '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido/expirado → cerrar sesión.
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  },
)

/** Extrae un mensaje de error legible de una respuesta de la API. */
export function apiError(error: unknown, fallback = 'Ha ocurrido un error'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
    return error.message
  }
  return fallback
}
