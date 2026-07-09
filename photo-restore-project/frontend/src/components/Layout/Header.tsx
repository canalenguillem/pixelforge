import { Camera } from 'lucide-react'

/** Barra superior de la aplicación. Placeholder inicial. */
export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6">
      <div className="flex items-center gap-2 font-semibold">
        <Camera className="h-5 w-5 text-primary" />
        <span>Photo Restore Pro</span>
      </div>
      {/* TODO: menú de usuario, notificaciones, toggle de tema */}
      <div className="text-sm text-muted-foreground">v1.0.0-alpha</div>
    </header>
  )
}
