import { Camera, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/auth.service'

/** Barra superior: marca + usuario + cerrar sesión. */
export function Header() {
  const { user, refreshToken, logout } = useAuthStore()

  async function handleLogout() {
    try {
      if (refreshToken) await authService.logout(refreshToken)
    } catch {
      // logout es idempotente; ignoramos errores de red
    } finally {
      logout()
    }
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6">
      <div className="flex items-center gap-2 font-semibold">
        <Camera className="h-5 w-5 text-primary" />
        <span>PixelForge</span>
      </div>
      <div className="flex items-center gap-4">
        {user && <span className="text-sm text-muted-foreground">{user.username}</span>}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <LogOut className="h-4 w-4" /> Salir
        </button>
      </div>
    </header>
  )
}
