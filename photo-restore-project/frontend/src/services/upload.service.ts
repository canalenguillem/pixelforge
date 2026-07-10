import { api } from './api'
import type { Upload } from '@/types'

export const uploadService = {
  async upload(file: File): Promise<Upload> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<Upload>('/uploads', form)
    return data
  },

  async list(page = 1, pageSize = 20) {
    const { data } = await api.get('/uploads', { params: { page, page_size: pageSize } })
    return data as { items: Upload[]; total: number; page: number; page_size: number }
  },

  /** Sube un PDF y crea un upload por cada foto extraída. */
  async uploadPdf(file: File) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/uploads/pdf', form, { timeout: 300_000 })
    return data as { items: Upload[]; total: number }
  },

  /** Rota el original 90° a izquierda o derecha (in-place). */
  async rotate(id: number, direction: 'left' | 'right'): Promise<Upload> {
    const { data } = await api.post(`/uploads/${id}/rotate`, null, { params: { direction } })
    return data as Upload
  },

  /** Borra un upload y en cascada todos sus procesados. */
  async remove(id: number): Promise<void> {
    await api.delete(`/uploads/${id}`)
  },
}
