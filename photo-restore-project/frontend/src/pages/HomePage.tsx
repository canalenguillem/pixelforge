import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, RotateCcw, Download, Images } from 'lucide-react'
import { UploadZone } from '@/components/Upload/UploadZone'
import { BeforeAfterSlider } from '@/components/Editor/BeforeAfterSlider'
import { ProcessPanel } from '@/components/Editor/ProcessPanel'
import { uploadService } from '@/services/upload.service'
import { jobService } from '@/services/job.service'
import { apiError } from '@/services/api'
import type { Job, Upload } from '@/types'

type Phase = 'idle' | 'uploading' | 'ready' | 'done'

export function HomePage() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [beforeUrl, setBeforeUrl] = useState<string | null>(null)
  const [afterUrl, setAfterUrl] = useState<string | null>(null)
  const [upload, setUpload] = useState<Upload | null>(null)
  const [elapsed, setElapsed] = useState<number | null>(null)

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

  async function handleDone(job: Job) {
    try {
      const blob = await jobService.result(job.id)
      setAfterUrl(URL.createObjectURL(blob))
      setElapsed(job.processing_time_seconds)
      setPhase('done')
    } catch (err) {
      setError(apiError(err, 'No se pudo obtener el resultado'))
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
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Restaurar foto</h1>
          <p className="text-muted-foreground">
            Sube una foto antigua y recupérala. Para encadenar procesos, usa la galería.
          </p>
        </div>
        <Link to="/galeria" className="flex shrink-0 items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm hover:bg-muted">
          <Images className="h-4 w-4" /> Galería
        </Link>
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

      {phase === 'ready' && upload && beforeUrl && (
        <ProcessPanel source={{ uploadId: upload.id, imageUrl: beforeUrl }} onDone={handleDone} />
      )}

      {phase === 'done' && beforeUrl && afterUrl && (
        <div className="space-y-4">
          <BeforeAfterSlider beforeSrc={beforeUrl} afterSrc={afterUrl} />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">{elapsed != null && `Procesada en ${elapsed}s`}</p>
            <div className="flex flex-wrap gap-3">
              {upload && (
                <Link
                  to={`/galeria/${upload.id}`}
                  className="flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
                >
                  <Images className="h-4 w-4" /> Seguir editando
                </Link>
              )}
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
