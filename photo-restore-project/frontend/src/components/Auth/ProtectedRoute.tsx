import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

/** Envuelve rutas privadas: redirige a /login si no hay sesión. */
export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => Boolean(s.accessToken))
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
