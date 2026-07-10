import { useEffect, useState } from 'react'
import { api } from '@/services/api'
import { cn } from '@/lib/utils'

interface AuthImageProps {
  /** Ruta de la API que devuelve una imagen (p. ej. /uploads/2/download). */
  src: string
  alt?: string
  className?: string
  onClick?: () => void
}

/**
 * Muestra una imagen servida por la API (requiere Bearer token): la descarga
 * como blob vía axios y la pinta con un object URL.
 */
export function AuthImage({ src, alt, className, onClick }: AuthImageProps) {
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    let objectUrl: string | null = null
    let cancelled = false
    api
      .get(src, { responseType: 'blob' })
      .then((r) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(r.data as Blob)
        setUrl(objectUrl)
      })
      .catch(() => {})
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [src])

  if (!url) {
    return <div className={cn('animate-pulse bg-muted', className)} onClick={onClick} />
  }
  return <img src={url} alt={alt ?? ''} className={className} onClick={onClick} draggable={false} />
}
