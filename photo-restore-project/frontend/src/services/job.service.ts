import { api } from './api'
import { useAuthStore } from '@/store/authStore'
import type { Job } from '@/types'

export interface CreateJobPayload {
  upload_id: number
  restoration_strength?: number
  codeformer_fidelity?: number
}

export const jobService = {
  /** Encola un job de restauración (async). Devuelve el job en estado 'queued'. */
  async create(payload: CreateJobPayload): Promise<Job> {
    const { data } = await api.post<Job>('/jobs', payload)
    return data
  },

  /** Encola un job de inpaint (eliminar daño) con máscara. */
  async createInpaint(uploadId: number, mask: Blob, grow = 8): Promise<Job> {
    const form = new FormData()
    form.append('upload_id', String(uploadId))
    form.append('grow', String(grow))
    form.append('mask', mask, 'mask.png')
    const { data } = await api.post<Job>('/jobs/inpaint', form)
    return data
  },

  async get(id: number): Promise<Job> {
    const { data } = await api.get<Job>(`/jobs/${id}`)
    return data
  },

  /** Descarga la imagen restaurada como blob (para mostrarla con object URL). */
  async result(id: number): Promise<Blob> {
    const { data } = await api.get(`/jobs/${id}/result`, { responseType: 'blob' })
    return data as Blob
  },
}

/**
 * Espera a que un job termine mostrando progreso.
 * Primario: WebSocket en tiempo real. Fallback: polling si el WS falla.
 * Resuelve al completar; lanza si falla.
 */
export function waitForJob(jobId: number, onProgress: (pct: number) => void): Promise<void> {
  const token = useAuthStore.getState().accessToken ?? ''
  return new Promise<void>((resolve, reject) => {
    let settled = false
    const done = (fn: () => void) => {
      if (!settled) {
        settled = true
        fn()
      }
    }

    const poll = async () => {
      if (settled) return
      try {
        const job = await jobService.get(jobId)
        if (job.status === 'completed') return done(resolve)
        if (job.status === 'failed') {
          return done(() => reject(new Error(job.error_message || 'El procesamiento falló')))
        }
      } catch {
        /* reintentar */
      }
      if (!settled) setTimeout(poll, 2000)
    }

    try {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${location.host}/api/v1/jobs/${jobId}/stream?token=${encodeURIComponent(token)}`
      const ws = new WebSocket(url)

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (typeof msg.progress === 'number') onProgress(msg.progress)
          if (msg.status === 'completed') {
            ws.close()
            done(resolve)
          } else if (msg.status === 'failed') {
            ws.close()
            done(() => reject(new Error(msg.error || 'El procesamiento falló')))
          }
        } catch {
          /* ignorar mensajes no-JSON */
        }
      }
      ws.onerror = () => poll() // conexión WS fallida → fallback a polling
      ws.onclose = () => {
        if (!settled) poll()
      }
    } catch {
      poll()
    }
  })
}
