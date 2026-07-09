import { api } from './api'
import type { Job } from '@/types'

export interface CreateJobPayload {
  upload_id: number
  restoration_strength?: number
  codeformer_fidelity?: number
}

export const jobService = {
  /** Crea y procesa un job (síncrono por ahora; puede tardar ~10-40s). */
  async create(payload: CreateJobPayload): Promise<Job> {
    const { data } = await api.post<Job>('/jobs', payload, { timeout: 600_000 })
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
