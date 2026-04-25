"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { BookCard, type BookCardData } from "@/components/BookCard";
import { api } from "@/lib/api";

export default function LibraryPage() {
  const [recent, setRecent] = useState<any[]>([]);
  const [all, setAll] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [r, a] = await Promise.all([api.recent(), api.search("")]);
        setRecent(r.items);
        setAll(a.items);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <>
      <TopBar />
      <div className="shell" style={{ paddingTop: 44, paddingBottom: 96 }}>
        <span className="eyebrow">正在阅读</span>
        <h1 style={{ marginBottom: 24 }}>继续你的故事</h1>
        {error && <div className="error">{error}</div>}
        {loading ? (
          <div className="empty">加载中…</div>
        ) : recent.length === 0 ? (
          <div className="empty">
            书架还空空如也。<Link href="/search">去搜索</Link>一本书开启阅读吧。
          </div>
        ) : (
          <div className="book-grid">
            {recent.map((b: any) => (
              <BookCard
                key={b.book_id}
                book={{
                  id: b.book_id,
                  title: b.title,
                  author: b.author,
                  cover_url: b.cover_url,
                  file_format: b.file_format,
                  progress_percent: b.progress_percent,
                } as BookCardData}
              />
            ))}
          </div>
        )}

        <div style={{ marginTop: 64 }}>
          <span className="eyebrow">书库</span>
          <h2
            style={{
              marginBottom: 24,
              borderBottom: "1px solid var(--rule)",
              paddingBottom: 14,
            }}
          >
            最新入库
          </h2>
          {all.length === 0 ? (
            <div className="empty">书库为空。</div>
          ) : (
            <div className="book-grid">
              {all.slice(0, 18).map((b: any) => (
                <BookCard key={b.id} book={b as BookCardData} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
