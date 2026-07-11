import { useEffect, useState } from 'react'
import { X, ZoomIn, ZoomOut } from 'lucide-react'

interface LightboxProps {
  src: string
  onClose: () => void
}

/**
 * Visor a pantalla completa. Abre la imagen grande (ajustada a la ventana);
 * clic en la imagen alterna zoom a tamaño real (con scroll/pan). Cierra con
 * Esc, la X o clic en el fondo.
 */
export function Lightbox({ src, onClose }: LightboxProps) {
  const [zoomed, setZoomed] = useState(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-2 sm:p-6"
      onClick={onClose}
    >
      <button
        onClick={onClose}
        className="absolute right-4 top-4 z-10 rounded-md bg-white/10 p-2 text-white hover:bg-white/20"
        title="Cerrar (Esc)"
      >
        <X className="h-5 w-5" />
      </button>
      <span className="absolute left-4 top-4 z-10 flex items-center gap-1.5 rounded-md bg-white/10 px-2 py-1 text-xs text-white">
        {zoomed ? <ZoomOut className="h-4 w-4" /> : <ZoomIn className="h-4 w-4" />}
        {zoomed ? 'Tamaño real — clic para ajustar' : 'Clic para ampliar'}
      </span>

      <div
        className={zoomed ? 'h-full w-full overflow-auto' : 'flex h-full w-full items-center justify-center'}
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={src}
          alt=""
          draggable={false}
          onClick={() => setZoomed((z) => !z)}
          className={
            zoomed
              ? 'max-w-none cursor-zoom-out'
              : 'max-h-[92vh] max-w-[95vw] cursor-zoom-in object-contain'
          }
        />
      </div>
    </div>
  )
}
