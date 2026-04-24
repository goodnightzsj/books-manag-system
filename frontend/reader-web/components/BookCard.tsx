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
  return (
    <Link href={`/read/${book.id}`} className="book-card">
      <div className="book-cover" style={cover as any}>
        {!book.cover_url && (
          <span style={{ fontSize: 56, fontFamily: "var(--font-serif)" }}>
            {initial(book.title)}
          </span>
        )}
        {book.rating != null && <span className="rating">★ {book.rating.toFixed(1)}</span>}
      </div>
      <div className="book-meta">
        <div className="title">{book.title}</div>
        <div className="author">
          {book.author ?? "佚名"}
          {book.file_format ? ` · ${String(book.file_format).toUpperCase()}` : ""}
        </div>
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
