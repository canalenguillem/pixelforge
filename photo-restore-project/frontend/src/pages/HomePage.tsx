import { useRef, useState } from 'react'
import { Loader2, RotateCcw, Download, Sparkles, Eraser, Brush, Trash2 } from 'lucide-react'
import { UploadZone } from '@/components/Upload/UploadZone'
import { BeforeAfterSlider } from '@/components/Editor/BeforeAfterSlider'
import { MaskEditor, type MaskEditorHandle } from '@/components/Editor/MaskEditor'
import { uploadService } from '@/services/upload.service'
import { jobService, waitForJob } from '@/services/job.service'
import { apiError } from '@/services/api'
import type { Upload } from '@/types'

type Phase = 'idle' | 'uploading' | 'ready' | 'processing' | 'done'
type Mode = 'restore' | 'inpaint'

export function HomePage() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [mode, setMode] = useState<Mode>('restore')
  const [error, setError] = useState<string | null>(null)

  const [beforeUrl, setBeforeUrl] = useState<string | null>(null)
  const [afterUrl, setAfterUrl] = useState<string | null>(null)
  const [upload, setUpload] = useState<Upload | null>(null)
  const [elapsed, setElapsed] = useState<number | null>(null)

  const [strength, setStrength] = useState(0.35)
  const [fidelity, setFidelity] = useState(0.5)
  const [brushSize, setBrushSize] = useState(24)
  const [progress, setProgress] = useState(0)

  const maskRef = useRef<MaskEditorHandle>(null)
  const processing = phase === 'processing'

  async function handleFile(file: File) {
    setError(null)
    setPhase('uploading')
    setBeforeUrl(URL.createObjectURL(file))
    setAfterUrl(null)
    try {
      const up = await uploadService.upload(file)
      setUpload(up)
      setPhase('ready')
    } catch (err) {
      setError(apiError(err, 'No se pudo subir la foto'))
      setPhase('idle')
    }
  }

  async function runJob(create: () => Promise<{ id: number }>, failMsg: string) {
    setError(null)
    setProgress(0)
    setPhase('processing')
    try {
      const job = await create()
      await waitForJob(job.id, setProgress)
      const final = await jobService.get(job.id)
      const blob = await jobService.result(job.id)
      setAfterUrl(URL.createObjectURL(blob))
      setElapsed(final.processing_time_seconds)
      setPhase('done')
    } catch (err) {
      setError(apiError(err, failMsg))
      setPhase('ready')
    }
  }

  function handleRestore() {
    if (!upload) return
    void runJob(
      () => jobService.create({ upload_id: upload.id, restoration_strength: strength, codeformer_fidelity: fidelity }),
      'La restauración falló',
    )
  }

  async function handleInpaint() {
    if (!upload) return
    const mask = await maskRef.current?.exportMask()
    if (!mask) {
      setError('No se pudo generar la máscara')
      return
    }
    void runJob(() => jobService.createInpaint(upload.id, mask), 'La eliminación de manchas falló')
  }

  function reset() {
    setPhase('idle')
    setUpload(null)
    setBeforeUrl(null)
    setAfterUrl(null)
    setError(null)
    setElapsed(null)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Restaurar foto</h1>
        <p className="text-muted-foreground">
          Recupera fotos antiguas: reenfoque y rostros, o elimina manchas pintándolas.
        </p>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p>
      )}

      {phase === 'idle' && <UploadZone onFile={handleFile} />}

      {phase === 'uploading' && (
        <div className="flex items-center justify-center gap-2 rounded-xl border border-border p-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" /> Subiendo…
        </div>
      )}

      {(phase === 'ready' || processing) && beforeUrl && (
        <div className="space-y-5">
          {/* Selector de modo */}
          <div className="flex gap-2 rounded-lg bg-muted p-1">
            <ModeTab active={mode === 'restore'} disabled={processing} onClick={() => setMode('restore')} icon={Sparkles} label="Restaurar" />
            <ModeTab active={mode === 'inpaint'} disabled={processing} onClick={() => setMode('inpaint')} icon={Eraser} label="Quitar manchas" />
          </div>

          {mode === 'restore' ? (
            <img
              src={beforeUrl}
              alt="Original"
              className="max-h-[50vh] w-full rounded-xl border border-border object-contain"
            />
          ) : (
            <MaskEditor ref={maskRef} imageUrl={beforeUrl} brushSize={brushSize} />
          )}

          <div className="space-y-4 rounded-xl border border-border p-5">
            {mode === 'restore' ? (
              <>
                <Slider
                  label="Fuerza de restauración"
                  hint={strength < 0.32 ? 'fiel' : strength > 0.42 ? 'agresiva' : 'equilibrada'}
                  min={0.2} max={0.5} step={0.05} value={strength} onChange={setStrength} disabled={processing}
                  format={(v) => v.toFixed(2)}
                />
                <Slider
                  label="Fidelidad de rostros"
                  hint={fidelity <= 0.5 ? 'más calidad' : 'más fiel'}
                  min={0} max={1} step={0.1} value={fidelity} onChange={setFidelity} disabled={processing}
                  format={(v) => v.toFixed(2)}
                />
              </>
            ) : (
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Slider
                    label="Tamaño del pincel"
                    hint="pinta sobre el daño"
                    min={6} max={80} step={2} value={brushSize} onChange={setBrushSize} disabled={processing}
                    format={(v) => `${v}px`}
                  />
                </div>
                <button
                  onClick={() => maskRef.current?.clear()}
                  disabled={processing}
                  className="mt-5 flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm hover:bg-muted disabled:opacity-50"
                >
                  <Trash2 className="h-4 w-4" /> Limpiar
                </button>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={mode === 'restore' ? handleRestore : handleInpaint}
                disabled={processing}
                className="flex flex-1 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {processing ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Procesando…</>
                ) : mode === 'restore' ? (
                  <><Sparkles className="h-4 w-4" /> Restaurar</>
                ) : (
                  <><Brush className="h-4 w-4" /> Quitar manchas</>
                )}
              </button>
              <button
                onClick={reset}
                disabled={processing}
                className="flex items-center gap-2 rounded-md border border-border px-4 py-2.5 text-sm hover:bg-muted disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" /> Otra
              </button>
            </div>

            {processing && (
              <div className="space-y-1.5">
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-300"
                    style={{ width: `${Math.round(progress * 100)}%` }}
                  />
                </div>
                <p className="text-center text-xs text-muted-foreground">
                  {progress > 0 ? `Procesando en ComfyUI… ${Math.round(progress * 100)}%` : 'En cola / cargando modelos…'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {phase === 'done' && beforeUrl && afterUrl && (
        <div className="space-y-4">
          <BeforeAfterSlider beforeSrc={beforeUrl} afterSrc={afterUrl} />
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{elapsed != null && `Procesada en ${elapsed}s`}</p>
            <div className="flex gap-3">
              <a
                href={afterUrl}
                download="resultado.png"
                className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                <Download className="h-4 w-4" /> Descargar
              </a>
              <button
                onClick={reset}
                className="flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
              >
                <RotateCcw className="h-4 w-4" /> Otra foto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ModeTab({
  active, disabled, onClick, icon: Icon, label,
}: {
  active: boolean
  disabled?: boolean
  onClick: () => void
  icon: typeof Sparkles
  label: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${
        active ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
      }`}
    >
      <Icon className="h-4 w-4" /> {label}
    </button>
  )
}

interface SliderProps {
  label: string
  hint: string
  min: number
  max: number
  step: number
  value: number
  onChange: (v: number) => void
  disabled?: boolean
  format: (v: number) => string
}

function Slider({ label, hint, min, max, step, value, onChange, disabled, format }: SliderProps) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">
          {format(value)} · {hint}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-primary disabled:opacity-50"
      />
    </div>
  )
}
