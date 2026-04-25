"use client";

/**
 * Loading placeholder grid that mirrors the `book-grid` layout. The
 * shimmer is a calm linear-gradient sweep — slower than the AI-template
 * default 0.8s, and only on `--bg-muted` so the page never feels like
 * it's blinking.
 */
export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="book-grid" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skel-cover skeleton-block" />
          <div className="skel-line skeleton-block" />
          <div className="skel-line short skeleton-block last" />
        </div>
      ))}
    </div>
  );
}
