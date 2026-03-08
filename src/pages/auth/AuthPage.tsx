import type React from 'react'
import type { AuthMode, StatusType } from '../../types'

type AuthPageProps = {
  mode: AuthMode
  isSubmitting: boolean
  statusType: StatusType
  statusMessage: string
  onSwitchMode: (mode: AuthMode) => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
}

const tabStyles = (active: boolean) =>
  [
    'flex-1 rounded-full px-4 py-2 text-sm font-semibold transition',
    active ? 'bg-white text-slate-900 shadow' : 'text-slate-600 hover:text-slate-900',
  ].join(' ')

export function AuthPage({
  mode,
  isSubmitting,
  statusType,
  statusMessage,
  onSwitchMode,
  onSubmit,
}: AuthPageProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-32 top-12 h-72 w-72 rounded-full bg-indigo-500/40 blur-[120px]" />
        <div className="absolute right-0 top-0 h-96 w-96 rounded-full bg-cyan-400/30 blur-[140px]" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-emerald-400/20 blur-[140px]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-12 lg:flex-row lg:items-center">
        <section className="flex-1 text-white">
          <p className="mb-3 inline-flex items-center rounded-full border border-white/20 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white/80">
            Human Resources Platform
          </p>
          <h1 className="font-display text-4xl font-semibold leading-tight sm:text-5xl">
            Build the HR workspace your team actually wants to use.
          </h1>
          <p className="mt-4 max-w-xl text-base text-white/80 sm:text-lg">
            Centralize onboarding, records, and workflows with a calm, secure hub. Start with email
            authentication and extend to SSO when you are ready.
          </p>

          <div className="mt-8 grid max-w-xl grid-cols-1 gap-4 text-sm text-white/70 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">Secure by default</p>
              <p className="mt-2 text-white/80">
                Keep employee data protected with modern auth and audit-ready flows.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">Fast rollout</p>
              <p className="mt-2 text-white/80">
                Ship a clean, responsive login and expand features incrementally.
              </p>
            </div>
          </div>
        </section>

        <section className="flex w-full max-w-md flex-1 flex-col rounded-3xl border border-white/10 bg-white/95 p-6 shadow-2xl shadow-black/40 backdrop-blur">
          <div className="rounded-full bg-slate-100 p-1 text-sm font-medium">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => onSwitchMode('signin')}
                className={tabStyles(mode === 'signin')}
                aria-pressed={mode === 'signin'}
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => onSwitchMode('signup')}
                className={tabStyles(mode === 'signup')}
                aria-pressed={mode === 'signup'}
              >
                Sign up
              </button>
            </div>
          </div>

          <div className="mt-6">
            <h2 className="text-2xl font-semibold text-slate-900">
              {mode === 'signin' ? 'Welcome back' : 'Create your account'}
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              {mode === 'signin'
                ? 'Use your work email and password to continue.'
                : 'Set up a secure account for your HR workspace.'}
            </p>
          </div>

          <form
            className="mt-6 flex flex-col gap-4"
            onSubmit={onSubmit}
          >
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              Email
              <input
                type="email"
                name="email"
                placeholder="you@company.com"
                autoComplete="email"
                className="h-11 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-indigo-200"
                disabled={isSubmitting}
                required
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              Password
              <input
                type="password"
                name="password"
                placeholder="••••••••"
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                className="h-11 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-indigo-200"
                disabled={isSubmitting}
                required
              />
            </label>

            {mode === 'signup' && (
              <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
                Confirm password
                <input
                  type="password"
                  name="confirmPassword"
                  placeholder="Repeat password"
                  autoComplete="new-password"
                  className="h-11 rounded-xl border border-slate-200 bg-white px-4 text-slate-900 shadow-sm outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-indigo-200"
                  disabled={isSubmitting}
                  required
                />
              </label>
            )}

            {statusType !== 'idle' && (
              <p
                className={`text-sm ${
                  statusType === 'success' ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {statusMessage}
              </p>
            )}

            <button
              type="submit"
              className="mt-2 inline-flex h-11 items-center justify-center rounded-full bg-slate-900 px-6 text-sm font-semibold text-white shadow transition hover:bg-slate-800"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? mode === 'signin'
                  ? 'Signing in...'
                  : 'Creating account...'
                : mode === 'signin'
                  ? 'Sign in'
                  : 'Create account'}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}
