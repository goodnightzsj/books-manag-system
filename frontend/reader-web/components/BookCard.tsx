"use client";
import Link from "next/link";

export type BookCardData = {
  id: string;
  title: string;
  author?: string | null;
  cover_url?: string | null;
  file_format?: string | null;
  rating?: number | null;
  progress_percent?: number;
};

function initial(title: string): string {
  const ch = title.trim().charAt(0);
  return ch || "?";
}

export function BookCard({ book }: { book: BookCardData }) {
  const cover = book.cover_url
    ? { backgroundImage: `url(${book.cover_url})` }
    : {};
  const fmt = book.file_format
    ? String(book.file_format).toUpperCase()
    : null;
  return (
    <Link href={`/read/${book.id}`} className="book-card">
      <div className="book-cover" style={cover as React.CSSProperties}>
        {!book.cover_url && (
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 60,
              fontWeight: 600,
              color: "rgba(244, 239, 226, 0.92)",
              letterSpacing: "-0.02em",
              lineHeight: 1,
            }}
          >
            {initial(book.title)}
          </span>
        )}
      </div>
      <div className="book-meta">
        <div className="title">{book.title}</div>
        <div className="author">
          {book.author ?? "佚名"}
          {fmt ? ` · ${fmt}` : ""}
        </div>
        {book.rating != null && (
          <div className="rating">★ {book.rating.toFixed(1)}</div>
        )}
        {typeof book.progress_percent === "number" && (
          <>
            <div className="progress">已读 {Math.round(book.progress_percent)}%</div>
            <div className="progress-rail">
              <span style={{ width: `${Math.min(100, book.progress_percent)}%` }} />
            </div>
          </>
        )}
      </div>
    </Link>
  );
}
