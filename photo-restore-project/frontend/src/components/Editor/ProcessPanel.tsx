import { useRef, useState } from 'react'
import { Loader2, Sparkles, Eraser, Brush, Trash2, Zap } from 'lucide-react'
import { MaskEditor, type MaskEditorHandle } from '@/components/Editor/MaskEditor'
import { jobService, waitForJob, type CreateJobPayload } from '@/services/job.service'
import { apiError } from '@/services/api'
import type { Job, WorkflowMode } from '@/types'

export interface ProcessSource {
  uploadId: number
  /** Si se indica, se procesa el resultado de ese job (encadenado). */
  parentJobId?: number
  /** URL cargable de la imagen a procesar (para preview y máscara). */
  imageUrl: string
}

interface ProcessPanelProps {
  source: ProcessSource
  onDone: (job: Job) => void
}

type Mode = 'restore' | 'inpaint'

/** Controles de procesado para una imagen fuente (original o resultado). */
export function ProcessPanel({ source, onDone }: ProcessPanelProps) {
  const [mode, setMode] = useState<Mode>('restore')
  const [engine, setEngine] = useState<WorkflowMode>('epic')
  const [strength, setStrength] = useState(0.35)
  const [fidelity, setFidelity] = useState(0.5)
  const [fluxDenoise, setFluxDenoise] = useState(0.85)
  const [enableHdr, setEnableHdr] = useState(false)
  const [brushSize, setBrushSize] = useState(24)
  const [progress, setProgress] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const maskRef = useRef<MaskEditorHandle>(null)

  async function runJob(create: () => Promise<Job>) {
    setError(null)
    setProgress(0)
    setProcessing(true)
    try {
      const job = await create()
      await waitForJob(job.id, setProgress)
      onDone(await jobService.get(job.id))
    } catch (err) {
      setError(apiError(err, 'El procesado falló'))
    } finally {
      setProcessing(false)
    }
  }

  function handleRestore() {
    const base = { upload_id: source.uploadId, parent_job_id: source.parentJobId }
    const payload: CreateJobPayload =
      engine === 'flux'
        ? { ...base, workflow_mode: 'flux', flux_denoise: fluxDenoise, enable_hdr_lora: enableHdr }
        : { ...base, workflow_mode: 'epic', restoration_strength: strength, codeformer_fidelity: fidelity }
    void runJob(() => jobService.create(payload))
  }

  async function handleInpaint() {
    const mask = await maskRef.current?.exportMask()
    if (!mask) {
      setError('Pinta sobre el daño antes de continuar')
      return
    }
    void runJob(() => jobService.createInpaint(source.uploadId, mask, 8, source.parentJobId))
  }

  return (
    <div className="space-y-5">
      {error && (
        <p className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p>
      )}

      <div className="flex gap-2 rounded-lg bg-muted p-1">
        <Tab active={mode === 'restore'} disabled={processing} onClick={() => setMode('restore')} icon={Sparkles} label="Restaurar" />
        <Tab active={mode === 'inpaint'} disabled={processing} onClick={() => setMode('inpaint')} icon={Eraser} label="Quitar manchas" />
      </div>

      {mode === 'restore' ? (
        <img
          src={source.imageUrl}
          alt="Fuente"
          className="max-h-[45vh] w-full rounded-xl border border-border object-contain"
        />
      ) : (
        <MaskEditor ref={maskRef} imageUrl={source.imageUrl} brushSize={brushSize} />
      )}

      <div className="space-y-4 rounded-xl border border-border p-5">
        {mode === 'restore' ? (
          <>
            <div className="flex gap-2 rounded-lg bg-muted p-1">
              <Tab active={engine === 'epic'} disabled={processing} onClick={() => setEngine('epic')} icon={Sparkles} label="Epic · rápido" />
              <Tab active={engine === 'flux'} disabled={processing} onClick={() => setEngine('flux')} icon={Zap} label="Flux · calidad" />
            </div>
            {engine === 'epic' ? (
              <>
                <Slider label="Fuerza de restauración" hint={strength < 0.32 ? 'fiel' : strength > 0.42 ? 'agresiva' : 'equilibrada'}
                  min={0.2} max={0.5} step={0.05} value={strength} onChange={setStrength} disabled={processing} format={(v) => v.toFixed(2)} />
                <Slider label="Fidelidad de rostros" hint={fidelity <= 0.5 ? 'más calidad' : 'más fiel'}
                  min={0} max={1} step={0.1} value={fidelity} onChange={setFidelity} disabled={processing} format={(v) => v.toFixed(2)} />
              </>
            ) : (
              <>
                <Slider label="Fuerza de restauración" hint={fluxDenoise < 0.7 ? 'sutil' : fluxDenoise >= 0.95 ? 'completa' : 'fuerte'}
                  min={0.5} max={1} step={0.05} value={fluxDenoise} onChange={setFluxDenoise} disabled={processing} format={(v) => v.toFixed(2)} />
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={enableHdr} disabled={processing} onChange={(e) => setEnableHdr(e.target.checked)} className="accent-primary" />
                  HDR LoRA (más vibrancia)
                </label>
                <p className="rounded-md bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
                  Flux da mayor calidad pero es bastante más lento (~2 min, o más la primera vez) y puede colorizar.
                </p>
              </>
            )}
          </>
        ) : (
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Slider label="Tamaño del pincel" hint="pinta sobre el daño"
                min={6} max={80} step={2} value={brushSize} onChange={setBrushSize} disabled={processing} format={(v) => `${v}px`} />
            </div>
            <button onClick={() => maskRef.current?.clear()} disabled={processing}
              className="mt-5 flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm hover:bg-muted disabled:opacity-50">
              <Trash2 className="h-4 w-4" /> Limpiar
            </button>
          </div>
        )}

        <button
          onClick={mode === 'restore' ? handleRestore : handleInpaint}
          disabled={processing}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {processing ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Procesando…</>
          ) : mode === 'restore' ? (
            <><Sparkles className="h-4 w-4" /> Restaurar</>
          ) : (
            <><Brush className="h-4 w-4" /> Quitar manchas</>
          )}
        </button>

        {processing && (
          <div className="space-y-1.5">
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-primary transition-all duration-300" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
            <p className="text-center text-xs text-muted-foreground">
              {progress > 0 ? `Procesando en ComfyUI… ${Math.round(progress * 100)}%` : 'En cola / cargando modelos…'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function Tab({ active, disabled, onClick, icon: Icon, label }: {
  active: boolean; disabled?: boolean; onClick: () => void; icon: typeof Sparkles; label: string
}) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${
        active ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
      }`}>
      <Icon className="h-4 w-4" /> {label}
    </button>
  )
}

function Slider({ label, hint, min, max, step, value, onChange, disabled, format }: {
  label: string; hint: string; min: number; max: number; step: number
  value: number; onChange: (v: number) => void; disabled?: boolean; format: (v: number) => string
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">{format(value)} · {hint}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-primary disabled:opacity-50" />
    </div>
  )
}
