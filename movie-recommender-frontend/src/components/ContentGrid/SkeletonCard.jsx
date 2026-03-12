const SkeletonCard = () => {
  return (
    <div className="animate-pulse">
      {/* Poster skeleton */}
      <div
        className="relative aspect-[2/3] rounded-lg overflow-hidden"
        style={{ background: 'var(--color-bg-card)' }}
      >
        {/* Shimmer overlay */}
        <div className="absolute inset-0 skeleton-shimmer" />

        {/* Badge placeholders */}
        <div className="absolute top-2 right-2 w-12 h-6 rounded-full bg-white/10" />
        <div className="absolute top-10 right-2 w-10 h-5 rounded-full bg-white/10" />
      </div>

      {/* Text skeleton */}
      <div className="mt-3 space-y-2">
        {/* Title */}
        <div className="h-3.5 rounded-md bg-white/10 w-4/5" />
        <div className="h-3 rounded-md bg-white/10 w-3/5" />

        {/* Year + platform pills */}
        <div className="h-3 rounded-md bg-white/10 w-1/4" />
        <div className="flex gap-1 mt-1">
          <div className="h-4 w-14 rounded bg-white/10" />
          <div className="h-4 w-14 rounded bg-white/10" />
        </div>
      </div>
    </div>
  );
};

export default SkeletonCard;
