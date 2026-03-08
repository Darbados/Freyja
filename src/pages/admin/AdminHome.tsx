type AdminHomeProps = {
  onOpenUsers: () => void
}

export function AdminHome({ onOpenUsers }: AdminHomeProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Admin</p>
        <h1 className="mt-3 text-3xl font-semibold">Admin console</h1>
        <button
          type="button"
          onClick={onOpenUsers}
          className="mt-6 inline-flex items-center rounded-full bg-white px-5 py-2 text-sm font-semibold text-slate-900 shadow transition hover:bg-white/90"
        >
          Users
        </button>
      </div>
    </div>
  )
}
