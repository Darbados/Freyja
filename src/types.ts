export type AuthMode = 'signin' | 'signup'
export type StatusType = 'idle' | 'success' | 'error' | 'info'

export type ProfileForm = {
  firstName: string
  lastName: string
  birthday: string
  position: string
  seniority: string
}

export type AdminUser = {
  id: number
  email: string
  first_name?: string | null
  last_name?: string | null
  birthday?: string | null
  position?: string | null
  seniority?: string | null
  is_active?: boolean
  is_superuser?: boolean
  created_at?: string
}
