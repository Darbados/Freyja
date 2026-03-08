import type { AdminUser } from '../../types'

type AdminUsersListProps = {
  users: AdminUser[]
  onSelectUser: (userId: number) => void
  onGoProfile: () => void
}

export function AdminUsersList({ users, onSelectUser, onGoProfile }: AdminUsersListProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <div className="w-full max-w-3xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/60">Admin</p>
            <h1 className="mt-3 text-3xl font-semibold">Users</h1>
            <p className="mt-2 text-sm text-white/70">Showing up to 50 users.</p>
          </div>
          <button
            type="button"
            onClick={onGoProfile}
            className="inline-flex items-center rounded-full border border-white/20 px-4 py-2 text-sm font-semibold text-white/90 transition hover:border-white/40 hover:text-white"
          >
            Go to profile
          </button>
        </div>

        <div className="mt-6 divide-y divide-white/10 rounded-2xl border border-white/10 bg-white/5">
          {users.length === 0 ? (
            <div className="p-6 text-sm text-white/70">No users found.</div>
          ) : (
            users.map((user) => (
              <button
                key={user.id}
                type="button"
                onClick={() => onSelectUser(user.id)}
                className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition hover:bg-white/10"
              >
                <div>
                  <div className="text-sm font-semibold text-white">{user.email}</div>
                  <div className="mt-1 text-xs text-white/60">
                    {[user.first_name, user.last_name].filter(Boolean).join(' ') || 'No name'}
                  </div>
                </div>
                <span className="text-xs uppercase tracking-[0.3em] text-white/50">
                  {user.is_superuser ? 'Superuser' : 'User'}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
