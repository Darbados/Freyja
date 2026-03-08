type ProfileLandingProps = {
  userEmail: string
  onGoToProfile: () => void
}

export function ProfileLanding({ userEmail, onGoToProfile }: ProfileLandingProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Personal</p>
        <h1 className="mt-3 text-3xl font-semibold">Welcome back</h1>
        <p className="mt-3 text-base text-white/80">
          Signed in as <span className="font-semibold text-white">{userEmail}</span>.
        </p>
        <button
          type="button"
          onClick={onGoToProfile}
          className="mt-6 inline-flex items-center rounded-full bg-white px-5 py-2 text-sm font-semibold text-slate-900 shadow transition hover:bg-white/90"
        >
          Go to profile
        </button>
      </div>
    </div>
  )
}
