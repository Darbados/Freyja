type LoadingScreenProps = {
  message?: string
}

export function LoadingScreen({ message = 'Loading...' }: LoadingScreenProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
      {message}
    </div>
  )
}
