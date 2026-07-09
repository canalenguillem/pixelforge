import { useRef, useState } from 'react'

interface BeforeAfterSliderProps {
  beforeSrc: string
  afterSrc: string
}

/**
 * Visor comparativo antes/después con una barra deslizante.
 * Arrastra (o mueve el ratón pulsado) para revelar la imagen restaurada.
 */
export function BeforeAfterSlider({ beforeSrc, afterSrc }: BeforeAfterSliderProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState(50)

  function updateFromClientX(clientX: number) {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const pct = ((clientX - rect.left) / rect.width) * 100
    setPosition(Math.max(0, Math.min(100, pct)))
  }

  return (
    <div
      ref={containerRef}
      className="relative aspect-[3/2] w-full select-none overflow-hidden rounded-xl border border-border bg-muted"
      onMouseMove={(e) => e.buttons === 1 && updateFromClientX(e.clientX)}
      onClick={(e) => updateFromClientX(e.clientX)}
      onTouchMove={(e) => e.touches[0] && updateFromClientX(e.touches[0].clientX)}
    >
      {/* Después (fondo completo) */}
      <img
        src={afterSrc}
        alt="Restaurada"
        className="absolute inset-0 h-full w-full object-contain"
        draggable={false}
      />
      {/* Antes (misma caja, recortada por la derecha con clip-path) */}
      <img
        src={beforeSrc}
        alt="Original"
        className="absolute inset-0 h-full w-full object-contain"
        style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
        draggable={false}
      />

      <span className="absolute left-2 top-2 rounded bg-black/60 px-2 py-0.5 text-xs text-white">
        Antes
      </span>
      <span className="absolute right-2 top-2 rounded bg-black/60 px-2 py-0.5 text-xs text-white">
        Después
      </span>

      <div className="absolute top-0 bottom-0 w-0.5 bg-white shadow" style={{ left: `${position}%` }}>
        <div className="absolute top-1/2 left-1/2 flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white text-xs text-black shadow">
          ↔
        </div>
      </div>
    </div>
  )
}
