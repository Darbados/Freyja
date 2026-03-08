import type React from 'react'
import { useState } from 'react'
import type { ProfileForm, StatusType } from '../../types'
import { Details } from './Details'

type ProfilePageProps = {
  userEmail: string
  isSuperuser: boolean
  profileForm: ProfileForm
  setProfileForm: React.Dispatch<React.SetStateAction<ProfileForm>>
  isSavingProfile: boolean
  statusType: StatusType
  statusMessage: string
  avatarUrl: string | null
  onAvatarUpload: (file: File) => Promise<void>
  onAvatarDownload: () => Promise<void>
  onSave: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  onLogout: () => void
  onOpenAdmin: () => void
}

export function ProfilePage({
  userEmail,
  isSuperuser,
  profileForm,
  setProfileForm,
  isSavingProfile,
  statusType,
  statusMessage,
  avatarUrl,
  onAvatarUpload,
  onAvatarDownload,
  onSave,
  onLogout,
  onOpenAdmin,
}: ProfilePageProps) {
  const [isAvatarOpen, setIsAvatarOpen] = useState(false)

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <div className="relative w-full max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur">
        {isSuperuser && (
          <div className="absolute right-5 top-5">
            <Details items={[{ label: '💪', tooltip: 'Superuser' }]} />
          </div>
        )}
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Personal</p>
        <h1 className="mt-3 text-3xl font-semibold">Welcome back</h1>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                if (avatarUrl) {
                  setIsAvatarOpen(true)
                }
              }}
              className="h-14 w-14 overflow-hidden rounded-full border border-white/20 bg-white/10"
              title={avatarUrl ? 'View photo' : undefined}
              aria-label={avatarUrl ? 'View photo' : undefined}
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Profile"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-sm text-white/60">
                  —
                </div>
              )}
            </button>
            <label className="inline-flex cursor-pointer items-center rounded-full border border-white/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/80 transition hover:border-white/40 hover:text-white">
              Upload photo
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  if (file) {
                    void onAvatarUpload(file)
                  }
                  event.currentTarget.value = ''
                }}
              />
            </label>
            <button
              type="button"
              onClick={onAvatarDownload}
              className="inline-flex items-center rounded-full border border-white/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/80 transition hover:border-white/40 hover:text-white"
            >
              Download images
            </button>
          </div>
        </div>

        <p className="mt-4 text-base text-white/80">
          Signed in as <span className="font-semibold text-white">{userEmail}</span>.
        </p>
        {isSuperuser && (
          <button
            type="button"
            onClick={onOpenAdmin}
            className="mt-4 inline-flex items-center rounded-full border border-white/20 px-4 py-2 text-sm font-semibold text-white/90 transition hover:border-white/40 hover:text-white"
          >
            Open admin
          </button>
        )}

        <form
          className="mt-8 grid gap-4 text-left"
          onSubmit={onSave}
        >
          <label className="flex flex-col gap-2 text-sm font-medium text-white/80">
            First name
            <input
              type="text"
              value={profileForm.firstName}
              onChange={(event) =>
                setProfileForm((current) => ({ ...current, firstName: event.target.value }))
              }
              className="h-11 rounded-xl border border-white/10 bg-white/10 px-4 text-white shadow-sm outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
              disabled={isSavingProfile}
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-white/80">
            Last name
            <input
              type="text"
              value={profileForm.lastName}
              onChange={(event) =>
                setProfileForm((current) => ({ ...current, lastName: event.target.value }))
              }
              className="h-11 rounded-xl border border-white/10 bg-white/10 px-4 text-white shadow-sm outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
              disabled={isSavingProfile}
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-white/80">
            Birthday
            <input
              type="date"
              value={profileForm.birthday}
              onChange={(event) =>
                setProfileForm((current) => ({ ...current, birthday: event.target.value }))
              }
              className="h-11 rounded-xl border border-white/10 bg-white/10 px-4 text-white shadow-sm outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
              disabled={isSavingProfile}
            />
          </label>

          {isSuperuser && (
            <>
              <label className="flex flex-col gap-2 text-sm font-medium text-white/80">
                Position
                <input
                  type="text"
                  value={profileForm.position}
                  onChange={(event) =>
                    setProfileForm((current) => ({ ...current, position: event.target.value }))
                  }
                  className="h-11 rounded-xl border border-white/10 bg-white/10 px-4 text-white shadow-sm outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
                  disabled={isSavingProfile}
                />
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium text-white/80">
                Seniority
                <select
                  value={profileForm.seniority}
                  onChange={(event) =>
                    setProfileForm((current) => ({ ...current, seniority: event.target.value }))
                  }
                  className="h-11 rounded-xl border border-white/10 bg-white/10 px-4 text-white shadow-sm outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
                  disabled={isSavingProfile}
                >
                  <option value="">Select seniority</option>
                  <option value="Intern">Intern</option>
                  <option value="Junior">Junior</option>
                  <option value="Medim">Medim</option>
                  <option value="Senior">Senior</option>
                  <option value="Staff">Staff</option>
                  <option value="Principal">Principal</option>
                  <option value="VP">VP</option>
                  <option value="Director">Director</option>
                </select>
              </label>
            </>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="inline-flex items-center rounded-full bg-white px-5 py-2 text-sm font-semibold text-slate-900 shadow transition hover:bg-white/90"
              disabled={isSavingProfile}
            >
              {isSavingProfile ? 'Saving...' : 'Save'}
            </button>
            {statusType !== 'idle' && (
              <span
                className={`text-sm ${
                  statusType === 'success' ? 'text-emerald-200' : 'text-rose-200'
                }`}
              >
                {statusMessage}
              </span>
            )}
          </div>
        </form>

        <button
          type="button"
          onClick={onLogout}
          className="mt-6 inline-flex items-center rounded-full border border-white/20 px-4 py-2 text-sm font-semibold text-white/90 transition hover:border-white/40 hover:text-white"
        >
          Log out
        </button>
      </div>

      {isAvatarOpen && avatarUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-6">
          <button
            type="button"
            className="absolute inset-0"
            onClick={() => setIsAvatarOpen(false)}
            aria-label="Close photo"
          />
          <div className="relative z-10 w-full max-w-3xl">
            <img
              src={avatarUrl.replace('/avatar_200.webp', '/avatar_400.webp')}
              alt="Profile large"
              className="mx-auto max-h-[80vh] w-auto rounded-3xl border border-white/10 shadow-2xl"
            />
          </div>
        </div>
      )}
    </div>
  )
}
