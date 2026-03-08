import type { AdminUser } from '../../types'

type AdminUserDetailProps = {
  user: AdminUser | null
  onBack: () => void
  onGoProfile: () => void
}

export function AdminUserDetail({ user, onBack, onGoProfile }: AdminUserDetailProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Admin</p>
        <h1 className="mt-3 text-3xl font-semibold">User details</h1>
        {user ? (
          <div className="mt-6 grid gap-3 text-sm text-white/80">
            <div>
              <span className="text-white/60">ID:</span> {user.id}
            </div>
            <div>
              <span className="text-white/60">Email:</span> {user.email}
            </div>
            <div>
              <span className="text-white/60">Name:</span>{' '}
              {[user.first_name, user.last_name].filter(Boolean).join(' ') || '—'}
            </div>
            <div>
              <span className="text-white/60">Birthday:</span>{' '}
              {user.birthday ? user.birthday.slice(0, 10) : '—'}
            </div>
            <div>
              <span className="text-white/60">Position:</span> {user.position ?? '—'}
            </div>
            <div>
              <span className="text-white/60">Seniority:</span> {user.seniority ?? '—'}
            </div>
            <div>
              <span className="text-white/60">Active:</span> {user.is_active ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="text-white/60">Superuser:</span> {user.is_superuser ? 'Yes' : 'No'}
            </div>
          </div>
        ) : (
          <p className="mt-6 text-sm text-white/70">User not found.</p>
        )}
        <div className="mt-8 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center rounded-full bg-white px-5 py-2 text-sm font-semibold text-slate-900 shadow transition hover:bg-white/90"
          >
            Back to users
          </button>
          <button
            type="button"
            onClick={onGoProfile}
            className="inline-flex items-center rounded-full border border-white/20 px-4 py-2 text-sm font-semibold text-white/90 transition hover:border-white/40 hover:text-white"
          >
            Go to profile
          </button>
        </div>
      </div>
    </div>
  )
}
