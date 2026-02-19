export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5">
      <div className="mb-3 h-5 w-3/4 rounded bg-stone-200" />
      <div className="mb-2 h-4 w-full rounded bg-stone-100" />
      <div className="h-4 w-2/3 rounded bg-stone-100" />
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
