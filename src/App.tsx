import { type FormEvent, useEffect, useState } from 'react'
import { LoadingScreen } from './components/LoadingScreen'
import { AdminLayout } from './pages/admin/AdminLayout'
import { AuthPage } from './pages/auth/AuthPage'
import { ProfileRouter } from './pages/profile/ProfileRouter'
import type { AdminUser, AuthMode, ProfileForm, StatusType } from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const [mode, setMode] = useState<AuthMode>('signin')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusType, setStatusType] = useState<StatusType>('idle')
  const [statusMessage, setStatusMessage] = useState('')
  const [isLoadingUser, setIsLoadingUser] = useState(true)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [userId, setUserId] = useState<number | null>(null)
  const [isSuperuser, setIsSuperuser] = useState(false)
  const [avatarPath, setAvatarPath] = useState<string | null>(null)
  const [profileForm, setProfileForm] = useState<ProfileForm>({
    firstName: '',
    lastName: '',
    birthday: '',
    position: '',
    seniority: '',
  })
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [path, setPath] = useState(window.location.pathname)
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([])
  const [adminSelected, setAdminSelected] = useState<AdminUser | null>(null)
  const [adminLoading, setAdminLoading] = useState(false)
  const [adminError, setAdminError] = useState('')

  const resetStatus = () => {
    setStatusType('idle')
    setStatusMessage('')
  }

  const loadCurrentUser = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Unable to load user profile.')
      }

      const payload = (await response.json()) as {
        id: number
        email: string
        first_name?: string | null
        last_name?: string | null
        birthday?: string | null
        position?: string | null
        seniority?: string | null
        is_superuser?: boolean
        avatar_200_path?: string | null
      }
      setUserId(payload.id)
      setUserEmail(payload.email)
      setIsSuperuser(Boolean(payload.is_superuser))
      setProfileForm({
        firstName: payload.first_name ?? '',
        lastName: payload.last_name ?? '',
        birthday: payload.birthday ? payload.birthday.slice(0, 10) : '',
        position: payload.position ?? '',
        seniority: payload.seniority ?? '',
      })
      setAvatarPath(payload.avatar_200_path ?? null)
      if (path === '/' || path === '') {
        window.history.replaceState({}, '', '/profile')
        setPath('/profile')
      }
    } catch {
      localStorage.removeItem('authToken')
      setUserId(null)
      setUserEmail(null)
      setIsSuperuser(false)
      setAvatarPath(null)
    } finally {
      setIsLoadingUser(false)
    }
  }

  useEffect(() => {
    const handlePopState = () => {
      setPath(window.location.pathname)
    }
    window.addEventListener('popstate', handlePopState)

    const token = localStorage.getItem('authToken')
    if (!token) {
      setIsLoadingUser(false)
      return () => {
        window.removeEventListener('popstate', handlePopState)
      }
    }
    loadCurrentUser(token)

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  useEffect(() => {
    const isAdminRoute = path.startsWith('/admin')
    if (!userEmail || !isSuperuser || !isAdminRoute) {
      setAdminUsers([])
      setAdminSelected(null)
      setAdminError('')
      setAdminLoading(false)
      return
    }

    const token = localStorage.getItem('authToken')
    if (!token) {
      setAdminError('You are not signed in.')
      setAdminLoading(false)
      return
    }

    const fetchAdminData = async () => {
      setAdminLoading(true)
      setAdminError('')

      try {
        if (path === '/admin/users') {
          const response = await fetch(`${API_BASE_URL}/admin/users?limit=50&offset=0`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })

          if (!response.ok) {
            const payload = (await response.json().catch(() => null)) as { detail?: string } | null
            throw new Error(payload?.detail ?? 'Unable to load users.')
          }

          const payload = (await response.json()) as AdminUser[]
          setAdminUsers(payload)
          setAdminSelected(null)
        } else if (path.startsWith('/admin/users/')) {
          const id = Number(path.replace('/admin/users/', ''))
          if (!Number.isFinite(id)) {
            throw new Error('Invalid user id.')
          }
          const response = await fetch(`${API_BASE_URL}/admin/users/${id}`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })

          if (!response.ok) {
            const payload = (await response.json().catch(() => null)) as { detail?: string } | null
            throw new Error(payload?.detail ?? 'Unable to load user.')
          }

          const payload = (await response.json()) as AdminUser
          setAdminSelected(payload)
        }
      } catch (error) {
        setAdminError(error instanceof Error ? error.message : 'Unexpected error while loading admin.')
      } finally {
        setAdminLoading(false)
      }
    }

    fetchAdminData()
  }, [path, userEmail, isSuperuser])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetStatus()
    const form = event.currentTarget

    if (mode === 'signin') {
      const formData = new FormData(form)
      const email = String(formData.get('email') ?? '').trim()
      const password = String(formData.get('password') ?? '')

      setIsSubmitting(true)

      try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password }),
        })

        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as { detail?: string } | null
          throw new Error(payload?.detail ?? 'Unable to sign in.')
        }

        const payload = (await response.json()) as { access_token: string }
        localStorage.setItem('authToken', payload.access_token)
        await loadCurrentUser(payload.access_token)
        setStatusType('success')
        setStatusMessage('Signed in successfully.')
      } catch (error) {
        setStatusType('error')
        setStatusMessage(error instanceof Error ? error.message : 'Unexpected error while signing in.')
      } finally {
        setIsSubmitting(false)
      }
      return
    }

    const formData = new FormData(form)
    const email = String(formData.get('email') ?? '').trim()
    const password = String(formData.get('password') ?? '')
    const confirmPassword = String(formData.get('confirmPassword') ?? '')

    if (password !== confirmPassword) {
      setStatusType('error')
      setStatusMessage('Passwords do not match.')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null
        throw new Error(payload?.detail ?? 'Unable to create account.')
      }

      form.reset()
      setStatusType('success')
      setStatusMessage('Account created successfully. You can now sign in when auth is enabled.')
      setMode('signin')
    } catch (error) {
      setStatusType('error')
      setStatusMessage(error instanceof Error ? error.message : 'Unexpected error while creating account.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoadingUser) {
    return <LoadingScreen message="Loading your profile..." />
  }

  if (userEmail) {
    if (path.startsWith('/admin')) {
      return (
        <AdminLayout
          path={path}
          isSuperuser={isSuperuser}
          isLoading={adminLoading}
          error={adminError}
          users={adminUsers}
          selectedUser={adminSelected}
          onGoProfile={() => {
            window.history.pushState({}, '', '/profile')
            setPath('/profile')
          }}
          onGoUsers={() => {
            window.history.pushState({}, '', '/admin/users')
            setPath('/admin/users')
          }}
          onSelectUser={(selectedId: number) => {
            window.history.pushState({}, '', `/admin/users/${selectedId}`)
            setPath(`/admin/users/${selectedId}`)
          }}
        />
      )
    }

    return (
      <ProfileRouter
        path={path}
        userEmail={userEmail}
        isSuperuser={isSuperuser}
        profileForm={profileForm}
        setProfileForm={setProfileForm}
        isSavingProfile={isSavingProfile}
        statusType={statusType}
        statusMessage={statusMessage}
        avatarUrl={avatarPath ? `${API_BASE_URL}${avatarPath}` : null}
        onAvatarUpload={async (file: File) => {
          if (file.size > 5 * 1024 * 1024) {
            setStatusType('error')
            setStatusMessage('Image must be 5MB or smaller.')
            return
          }
          const token = localStorage.getItem('authToken')
          if (!token) {
            setStatusType('error')
            setStatusMessage('You are not signed in.')
            return
          }

          try {
            const formData = new FormData()
            formData.append('file', file)
            const response = await fetch(`${API_BASE_URL}/users/me/avatar`, {
              method: 'POST',
              headers: {
                Authorization: `Bearer ${token}`,
              },
              body: formData,
            })

            if (!response.ok) {
              const payload = (await response.json().catch(() => null)) as { detail?: string } | null
              throw new Error(payload?.detail ?? 'Unable to upload avatar.')
            }

            const payload = (await response.json()) as { avatar_200_path?: string | null }
            setAvatarPath(payload.avatar_200_path ?? null)
            setStatusType('success')
            setStatusMessage('Profile photo updated.')
          } catch (error) {
            setStatusType('error')
            setStatusMessage(error instanceof Error ? error.message : 'Unexpected error while uploading.')
          }
        }}
        onAvatarDownload={async () => {
          const token = localStorage.getItem('authToken')
          if (!token) {
            setStatusType('error')
            setStatusMessage('You are not signed in.')
            return
          }

          try {
            const response = await fetch(`${API_BASE_URL}/users/me/avatar/download`, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            })

            if (!response.ok) {
              const payload = (await response.json().catch(() => null)) as { detail?: string } | null
              throw new Error(payload?.detail ?? 'Unable to download images.')
            }

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = 'avatars.zip'
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
          } catch (error) {
            setStatusType('error')
            setStatusMessage(error instanceof Error ? error.message : 'Unexpected error while downloading.')
          }
        }}
        onSave={async (event) => {
          event.preventDefault()
          setIsSavingProfile(true)
          setStatusType('idle')
          setStatusMessage('')

          const token = localStorage.getItem('authToken')
          if (!token) {
            setStatusType('error')
            setStatusMessage('You are not signed in.')
            setIsSavingProfile(false)
            return
          }

          try {
            const isAdminUpdate = isSuperuser && userId !== null
            const endpoint = isAdminUpdate
              ? `${API_BASE_URL}/users/${userId}`
              : `${API_BASE_URL}/users/me`
            const response = await fetch(endpoint, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                first_name: profileForm.firstName || null,
                last_name: profileForm.lastName || null,
                birthday: profileForm.birthday ? profileForm.birthday : null,
                ...(isAdminUpdate
                  ? {
                      position: profileForm.position || null,
                      seniority: profileForm.seniority || null,
                    }
                  : {}),
              }),
            })

            if (!response.ok) {
              const payload = (await response.json().catch(() => null)) as { detail?: string } | null
              throw new Error(payload?.detail ?? 'Unable to save profile.')
            }

            const payload = (await response.json()) as {
              first_name?: string | null
              last_name?: string | null
              birthday?: string | null
              position?: string | null
              seniority?: string | null
            }
            setProfileForm({
              firstName: payload.first_name ?? '',
              lastName: payload.last_name ?? '',
              birthday: payload.birthday ? payload.birthday.slice(0, 10) : '',
              position: payload.position ?? profileForm.position,
              seniority: payload.seniority ?? profileForm.seniority,
            })
            setStatusType('success')
            setStatusMessage('Profile updated.')
          } catch (error) {
            setStatusType('error')
            setStatusMessage(error instanceof Error ? error.message : 'Unexpected error while saving.')
          } finally {
            setIsSavingProfile(false)
          }
        }}
        onLogout={() => {
          localStorage.removeItem('authToken')
          setUserEmail(null)
          setMode('signin')
          setAdminUsers([])
          setAdminSelected(null)
          setAdminError('')
          setAvatarPath(null)
          window.history.pushState({}, '', '/')
          setPath('/')
        }}
        onGoProfile={() => {
          window.history.pushState({}, '', '/profile')
          setPath('/profile')
        }}
        onOpenAdmin={() => {
          window.history.pushState({}, '', '/admin')
          setPath('/admin')
        }}
      />
    )
  }

  return (
    <AuthPage
      mode={mode}
      isSubmitting={isSubmitting}
      statusType={statusType}
      statusMessage={statusMessage}
      onSwitchMode={(nextMode) => {
        setMode(nextMode)
        resetStatus()
      }}
      onSubmit={handleSubmit}
    />
  )
}

export default App
