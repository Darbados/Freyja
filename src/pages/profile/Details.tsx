type DetailsProps = {
  items: Array<{ label: string; tooltip?: string }>
}

export function Details({ items }: DetailsProps) {
  const tooltip = items
    .map((item) => item.tooltip)
    .filter(Boolean)
    .join(' · ')

  return (
    <div
      className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm text-white/90"
      title={tooltip || undefined}
      aria-label={tooltip || undefined}
    >
      {items.map((item, index) => (
        <span key={`${item.label}-${index}`}>{item.label}</span>
      ))}
    </div>
  )
}
