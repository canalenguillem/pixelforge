import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ImageOff, Loader2, Trash2, FileUp, ImagePlus, RotateCcw, RotateCw } from 'lucide-react'
import { AuthImage } from '@/components/Common/AuthImage'
import { ProcessPanel } from '@/components/Editor/ProcessPanel'
import { api, apiError } from '@/services/api'
import { uploadService } from '@/services/upload.service'
import { jobService } from '@/services/job.service'
import type { Job, Upload } from '@/types'

export function GalleryPage() {
  const { uploadId } = useParams()
  return uploadId ? <UploadDetail uploadId={Number(uploadId)} /> : <UploadGrid />
}

// -----------------------------------------------------------------------------
// Grid de originales
// -----------------------------------------------------------------------------
function UploadGrid() {
  const [uploads, setUploads] = useState<Upload[] | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [rotating, setRotating] = useState<number | null>(null)
  const [versions, setVersions] = useState<Record<number, number>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()
  const pdfInput = useRef<HTMLInputElement>(null)
  const photoInput = useRef<HTMLInputElement>(null)

  async function handleRotate(id: number, direction: 'left' | 'right') {
    setRotating(id)
    try {
      await uploadService.rotate(id, direction)
      setVersions((v) => ({ ...v, [id]: (v[id] ?? 0) + 1 })) // fuerza recarga de la miniatura
    } catch {
      /* noop */
    } finally {
      setRotating(null)
    }
  }

  function load() {
    return uploadService
      .list(1, 100)
      .then((r) => setUploads(r.items))
      .catch(() => setUploads([]))
  }

  useEffect(() => {
    void load()
  }, [])

  async function handlePdf(file: File) {
    setNotice(null)
    setBusy('Extrayendo fotos del PDF…')
    try {
      const r = await uploadService.uploadPdf(file)
      await load()
      setNotice(`${r.total} foto(s) extraída(s) del PDF.`)
    } catch (err) {
      setNotice(apiError(err, 'No se pudo procesar el PDF'))
    } finally {
      setBusy(null)
    }
  }

  async function handlePhoto(file: File) {
    setNotice(null)
    setBusy('Subiendo foto…')
    try {
      await uploadService.upload(file)
      await load()
    } catch (err) {
      setNotice(apiError(err, 'No se pudo subir la foto'))
    } finally {
      setBusy(null)
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm('¿Borrar esta foto y TODOS sus procesados? No se puede deshacer.')) return
    setDeleting(id)
    try {
      await uploadService.remove(id)
      setUploads((prev) => (prev ? prev.filter((u) => u.id !== id) : prev))
    } catch {
      /* noop */
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Galería</h1>
          <p className="text-muted-foreground">Tus fotos subidas. Clica una para ver y encadenar procesados.</p>
        </div>
        <div className="flex gap-2">
          <input ref={photoInput} type="file" accept="image/*" hidden
            onChange={(e) => { const f = e.target.files?.[0]; if (f) void handlePhoto(f); e.target.value = '' }} />
          <input ref={pdfInput} type="file" accept="application/pdf" hidden
            onChange={(e) => { const f = e.target.files?.[0]; if (f) void handlePdf(f); e.target.value = '' }} />
          <button onClick={() => photoInput.current?.click()} disabled={!!busy}
            className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-muted disabled:opacity-50">
            <ImagePlus className="h-4 w-4" /> Subir foto
          </button>
          <button onClick={() => pdfInput.current?.click()} disabled={!!busy}
            className="flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50">
            <FileUp className="h-4 w-4" /> Subir PDF
          </button>
        </div>
      </div>

      {busy && (
        <p className="flex items-center gap-2 rounded-md bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> {busy}
        </p>
      )}
      {notice && <p className="rounded-md bg-muted/60 px-4 py-3 text-sm">{notice}</p>}

      {uploads === null ? (
        <Centered><Loader2 className="h-5 w-5 animate-spin" /> Cargando…</Centered>
      ) : uploads.length === 0 ? (
        <Centered>
          <ImageOff className="h-5 w-5" /> No hay fotos aún.{' '}
          <Link to="/" className="text-primary underline">Sube una</Link>
        </Centered>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {uploads.map((u) => (
            <div
              key={u.id}
              className="group relative overflow-hidden rounded-xl border border-border transition-colors hover:border-primary"
            >
              <button onClick={() => navigate(`/galeria/${u.id}`)} className="block w-full text-left">
                <AuthImage
                  src={`/uploads/${u.id}/download${versions[u.id] ? `?r=${versions[u.id]}` : ''}`}
                  className="aspect-square w-full bg-muted object-cover"
                />
                <div className="truncate px-3 py-2 text-xs text-muted-foreground">{u.original_filename}</div>
              </button>

              {/* Girar (izquierda / derecha) */}
              <div className="absolute left-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  onClick={() => handleRotate(u.id, 'left')}
                  disabled={rotating === u.id}
                  title="Girar a la izquierda"
                  className="rounded-md bg-black/60 p-1.5 text-white hover:bg-black/80 disabled:opacity-60"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleRotate(u.id, 'right')}
                  disabled={rotating === u.id}
                  title="Girar a la derecha"
                  className="rounded-md bg-black/60 p-1.5 text-white hover:bg-black/80 disabled:opacity-60"
                >
                  {rotating === u.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCw className="h-4 w-4" />}
                </button>
              </div>

              <button
                onClick={() => handleDelete(u.id)}
                disabled={deleting === u.id}
                title="Borrar foto y todos sus procesados"
                className="absolute right-2 top-2 rounded-md bg-black/60 p-1.5 text-white opacity-0 transition-opacity hover:bg-destructive group-hover:opacity-100 disabled:opacity-100"
              >
                {deleting === u.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Detalle de un upload: original + cadena de resultados + panel de proceso
// -----------------------------------------------------------------------------
interface SourceSel {
  parentJobId?: number
  apiPath: string
  label: string
}

function UploadDetail({ uploadId }: { uploadId: number }) {
  const [jobs, setJobs] = useState<Job[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sel, setSel] = useState<SourceSel>({ apiPath: `/uploads/${uploadId}/download`, label: 'Original' })
  const [selUrl, setSelUrl] = useState<string | null>(null)
  const navigate = useNavigate()

  async function handleDeleteUpload() {
    if (!window.confirm('¿Borrar esta foto y TODOS sus procesados? No se puede deshacer.')) return
    try {
      await uploadService.remove(uploadId)
      navigate('/galeria')
    } catch (err) {
      setError(apiError(err, 'No se pudo borrar'))
    }
  }

  async function refresh(selectJobId?: number) {
    try {
      const r = await jobService.list(uploadId, 100)
      setJobs(r.items)
      if (selectJobId) {
        selectSource({ parentJobId: selectJobId, apiPath: `/jobs/${selectJobId}/result`, label: `Resultado #${selectJobId}` })
      }
    } catch (err) {
      setError(apiError(err, 'No se pudieron cargar los procesados'))
      setJobs([])
    }
  }

  useEffect(() => {
    void refresh()
    selectSource({ apiPath: `/uploads/${uploadId}/download`, label: 'Original' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadId])

  // Carga el blob de la fuente seleccionada como object URL (para preview/máscara)
  function selectSource(s: SourceSel) {
    setSel(s)
    setSelUrl(null)
    api
      .get(s.apiPath, { responseType: 'blob' })
      .then((r) => setSelUrl(URL.createObjectURL(r.data as Blob)))
      .catch(() => setError('No se pudo cargar la imagen seleccionada'))
  }

  const completed = (jobs ?? []).filter((j) => j.status === 'completed')

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/galeria" className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted">
          <ArrowLeft className="h-4 w-4" /> Galería
        </Link>
        <h1 className="text-xl font-bold">Foto #{uploadId}</h1>
        <button
          onClick={handleDeleteUpload}
          title="Borrar foto y todos sus procesados"
          className="ml-auto flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10"
        >
          <Trash2 className="h-4 w-4" /> Borrar
        </button>
      </div>

      {error && <p className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p>}

      {/* Tira de imágenes: original + resultados. Clic = seleccionar como fuente. */}
      <div>
        <p className="mb-2 text-sm font-medium">Imágenes ({completed.length + 1})</p>
        <div className="flex gap-3 overflow-x-auto pb-2">
          <Thumb
            active={!sel.parentJobId}
            onClick={() => selectSource({ apiPath: `/uploads/${uploadId}/download`, label: 'Original' })}
            src={`/uploads/${uploadId}/download`}
            label="Original"
          />
          {completed.map((j) => (
            <Thumb
              key={j.id}
              active={sel.parentJobId === j.id}
              onClick={() => selectSource({ parentJobId: j.id, apiPath: `/jobs/${j.id}/result`, label: `#${j.id}` })}
              src={`/jobs/${j.id}/result`}
              label={jobLabel(j)}
              sublabel={j.parent_job_id ? `← #${j.parent_job_id}` : undefined}
            />
          ))}
        </div>
      </div>

      {/* Panel de proceso sobre la imagen seleccionada */}
      <div>
        <p className="mb-2 text-sm">
          Aplicar a: <span className="font-medium">{sel.label}</span>
        </p>
        {selUrl ? (
          <ProcessPanel
            key={sel.apiPath}
            source={{ uploadId, parentJobId: sel.parentJobId, imageUrl: selUrl }}
            onDone={(job) => refresh(job.id)}
          />
        ) : (
          <Centered><Loader2 className="h-5 w-5 animate-spin" /> Cargando imagen…</Centered>
        )}
      </div>
    </div>
  )
}

function Thumb({ active, onClick, src, label, sublabel }: {
  active: boolean; onClick: () => void; src: string; label: string; sublabel?: string
}) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 overflow-hidden rounded-lg border-2 text-left transition-colors ${
        active ? 'border-primary' : 'border-transparent hover:border-border'
      }`}
    >
      <AuthImage src={src} className="h-24 w-24 bg-muted object-cover" />
      <div className="w-24 px-1.5 py-1 text-[11px] leading-tight">
        <div className="truncate font-medium">{label}</div>
        {sublabel && <div className="truncate text-muted-foreground">{sublabel}</div>}
      </div>
    </button>
  )
}

function jobLabel(j: Job): string {
  if (j.job_type === 'inpaint') return 'Manchas'
  if (j.workflow_mode === 'flux') return `Flux ${j.params?.flux_denoise ?? ''}`.trim()
  return `Epic ${j.params?.restoration_strength ?? ''}`.trim()
}

function Centered({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-xl border border-border p-12 text-muted-foreground">
      {children}
    </div>
  )
}
