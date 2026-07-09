import { useState } from 'react'
import { Loader2, RotateCcw, Download, Sparkles } from 'lucide-react'
import { UploadZone } from '@/components/Upload/UploadZone'
import { BeforeAfterSlider } from '@/components/Editor/BeforeAfterSlider'
import { uploadService } from '@/services/upload.service'
import { jobService } from '@/services/job.service'
import { apiError } from '@/services/api'
import type { Upload } from '@/types'

type Phase = 'idle' | 'uploading' | 'ready' | 'processing' | 'done'

export function HomePage() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)

  const [beforeUrl, setBeforeUrl] = useState<string | null>(null)
  const [afterUrl, setAfterUrl] = useState<string | null>(null)
  const [upload, setUpload] = useState<Upload | null>(null)
  const [elapsed, setElapsed] = useState<number | null>(null)

  const [strength, setStrength] = useState(0.35)
  const [fidelity, setFidelity] = useState(0.5)

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

  async function handleRestore() {
    if (!upload) return
    setError(null)
    setPhase('processing')
    try {
      const job = await jobService.create({
        upload_id: upload.id,
        restoration_strength: strength,
        codeformer_fidelity: fidelity,
      })
      if (job.status !== 'completed') {
        throw new Error(job.error_message || 'El procesamiento falló')
      }
      const blob = await jobService.result(job.id)
      setAfterUrl(URL.createObjectURL(blob))
      setElapsed(job.processing_time_seconds)
      setPhase('done')
    } catch (err) {
      setError(apiError(err, 'La restauración falló'))
      setPhase('ready')
    }
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
          Sube una foto antigua y recupérala: reenfoque, limpieza y restauración de rostros.
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

      {(phase === 'ready' || phase === 'processing') && beforeUrl && (
        <div className="space-y-5">
          <img
            src={beforeUrl}
            alt="Original"
            className="max-h-[50vh] w-full rounded-xl border border-border object-contain"
          />

          <div className="space-y-4 rounded-xl border border-border p-5">
            <Slider
              label="Fuerza de restauración"
              hint={strength < 0.32 ? 'fiel' : strength > 0.42 ? 'agresiva' : 'equilibrada'}
              min={0.2}
              max={0.5}
              step={0.05}
              value={strength}
              onChange={setStrength}
              disabled={phase === 'processing'}
            />
            <Slider
              label="Fidelidad de rostros"
              hint={fidelity <= 0.5 ? 'más calidad' : 'más fiel'}
              min={0}
              max={1}
              step={0.1}
              value={fidelity}
              onChange={setFidelity}
              disabled={phase === 'processing'}
            />

            <div className="flex gap-3">
              <button
                onClick={handleRestore}
                disabled={phase === 'processing'}
                className="flex flex-1 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {phase === 'processing' ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Restaurando…
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" /> Restaurar
                  </>
                )}
              </button>
              <button
                onClick={reset}
                disabled={phase === 'processing'}
                className="flex items-center gap-2 rounded-md border border-border px-4 py-2.5 text-sm hover:bg-muted disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" /> Otra
              </button>
            </div>
            {phase === 'processing' && (
              <p className="text-center text-xs text-muted-foreground">
                Procesando en ComfyUI (la primera vez carga los modelos, puede tardar).
              </p>
            )}
          </div>
        </div>
      )}

      {phase === 'done' && beforeUrl && afterUrl && (
        <div className="space-y-4">
          <BeforeAfterSlider beforeSrc={beforeUrl} afterSrc={afterUrl} />
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {elapsed != null && `Restaurada en ${elapsed}s`}
            </p>
            <div className="flex gap-3">
              <a
                href={afterUrl}
                download="restaurada.png"
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

interface SliderProps {
  label: string
  hint: string
  min: number
  max: number
  step: number
  value: number
  onChange: (v: number) => void
  disabled?: boolean
}

function Slider({ label, hint, min, max, step, value, onChange, disabled }: SliderProps) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">
          {value.toFixed(2)} · {hint}
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
