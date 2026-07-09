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
}
