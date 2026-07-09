import { Link } from 'react-router-dom'

/** Página 404. Placeholder inicial. */
export function NotFoundPage() {
  return (
    <div className="text-center">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="mt-2 text-muted-foreground">Página no encontrada.</p>
      <Link to="/" className="mt-4 inline-block text-primary underline">
        Volver al inicio
      </Link>
    </div>
  )
}
