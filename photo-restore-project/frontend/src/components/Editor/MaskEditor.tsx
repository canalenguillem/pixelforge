import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'

export interface MaskEditorHandle {
  /** Exporta la máscara (blanco = reparar) al tamaño natural de la imagen. */
  exportMask: () => Promise<Blob | null>
  clear: () => void
}

interface Props {
  imageUrl: string
  brushSize: number // en píxeles de pantalla
}

type Point = { x: number; y: number; scale: number }

/**
 * Editor de máscara: pinta con pincel sobre el daño. Mantiene dos canvas:
 * uno visible (imagen + trazos rojos translúcidos) y otro oculto a resolución
 * natural (negro + trazos blancos) que se exporta como máscara PNG.
 */
export const MaskEditor = forwardRef<MaskEditorHandle, Props>(function MaskEditor(
  { imageUrl, brushSize },
  ref,
) {
  const displayRef = useRef<HTMLCanvasElement>(null)
  const maskRef = useRef<HTMLCanvasElement>(null)
  const drawing = useRef(false)
  const last = useRef<Point | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      const dc = displayRef.current
      const mc = maskRef.current
      if (!dc || !mc) return
      dc.width = mc.width = img.naturalWidth
      dc.height = mc.height = img.naturalHeight
      dc.getContext('2d')!.drawImage(img, 0, 0)
      const mctx = mc.getContext('2d')!
      mctx.fillStyle = 'black'
      mctx.fillRect(0, 0, mc.width, mc.height)
      setReady(true)
    }
    img.src = imageUrl
  }, [imageUrl])

  function toNatural(e: React.PointerEvent): Point {
    const dc = displayRef.current!
    const rect = dc.getBoundingClientRect()
    const scale = dc.width / rect.width
    return { x: (e.clientX - rect.left) * scale, y: (e.clientY - rect.top) * scale, scale }
  }

  function stroke(from: Point, to: Point, radius: number) {
    const layers: [CanvasRenderingContext2D, string][] = [
      [displayRef.current!.getContext('2d')!, 'rgba(239,68,68,0.55)'],
      [maskRef.current!.getContext('2d')!, 'white'],
    ]
    for (const [ctx, color] of layers) {
      ctx.strokeStyle = color
      ctx.fillStyle = color
      ctx.lineWidth = radius * 2
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.stroke()
      // punto inicial (para clics sin arrastre)
      ctx.beginPath()
      ctx.arc(to.x, to.y, radius, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  function onDown(e: React.PointerEvent) {
    drawing.current = true
    const p = toNatural(e)
    last.current = p
    stroke(p, p, brushSize * p.scale)
  }
  function onMove(e: React.PointerEvent) {
    if (!drawing.current) return
    const p = toNatural(e)
    if (last.current) stroke(last.current, p, brushSize * p.scale)
    last.current = p
  }
  function onUp() {
    drawing.current = false
    last.current = null
  }

  useImperativeHandle(ref, () => ({
    exportMask: () =>
      new Promise((resolve) => {
        maskRef.current?.toBlob((b) => resolve(b), 'image/png')
      }),
    clear: () => {
      const mc = maskRef.current
      const dc = displayRef.current
      if (!mc || !dc) return
      const mctx = mc.getContext('2d')!
      mctx.fillStyle = 'black'
      mctx.fillRect(0, 0, mc.width, mc.height)
      const img = new Image()
      img.onload = () => dc.getContext('2d')!.drawImage(img, 0, 0)
      img.src = imageUrl
    },
  }))

  return (
    <div>
      <canvas
        ref={displayRef}
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={onUp}
        onPointerLeave={onUp}
        className="w-full touch-none cursor-crosshair rounded-xl border border-border"
      />
      <canvas ref={maskRef} className="hidden" />
      {!ready && <p className="mt-2 text-sm text-muted-foreground">Cargando imagen…</p>}
    </div>
  )
})
