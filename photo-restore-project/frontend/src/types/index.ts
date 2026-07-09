export interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  avatar_url: string | null
  is_active: boolean
  email_verified: boolean
  created_at: string
  last_login: string | null
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Upload {
  id: number
  original_filename: string
  file_size: number | null
  mime_type: string | null
  width: number | null
  height: number | null
  status: string
  created_at: string
}

export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed'

export interface Job {
  id: number
  upload_id: number
  status: JobStatus
  job_type: string | null
  error_message: string | null
  processing_time_seconds: number | null
  created_at: string
  completed_at: string | null
}
