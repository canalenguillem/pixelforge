import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Camera, Loader2 } from 'lucide-react'
import { authService } from '@/services/auth.service'
import { apiError } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

/** Pantalla de acceso. El registro público está desactivado: el alta será por
 * invitación (link). Para reactivarlo, restaurar el modo 'register'. */
export function LoginPage() {
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const tokens = await authService.login(email, password)
      setTokens(tokens.access_token, tokens.refresh_token)
      setUser(await authService.me())
      navigate('/')
    } catch (err) {
      setError(apiError(err, 'No se pudo iniciar sesión'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-sm rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <Camera className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-xl font-semibold">PixelForge</h1>
          <p className="text-sm text-muted-foreground">Inicia sesión para restaurar tus fotos</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="tu@email.com"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Entrar
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          El acceso es por invitación.
        </p>
      </div>
    </div>
  )
}
