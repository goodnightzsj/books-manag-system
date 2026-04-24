"use client";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { BookCard, type BookCardData } from "@/components/BookCard";
import { api } from "@/lib/api";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    setLoading(true);
    setError(null);
    try {
      const r = await api.search(q);
      setItems(r.items);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <TopBar />
      <div className="shell" style={{ paddingTop: 40, paddingBottom: 80 }}>
        <div className="eyebrow">探索</div>
        <h1 style={{ marginBottom: 18 }}>搜索书库</h1>
        <form onSubmit={onSubmit} style={{ display: "flex", gap: 10, maxWidth: 600 }}>
          <input
            className="input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="书名、作者、ISBN 或标签"
          />
          <button className="btn primary" type="submit">
            搜索
          </button>
        </form>
        {error && <div className="error" style={{ marginTop: 20 }}>{error}</div>}
        <div style={{ marginTop: 32 }}>
          {loading ? (
            <div className="empty">搜索中…</div>
          ) : !touched ? (
            <div className="empty">输入关键字开始搜索。</div>
          ) : items.length === 0 ? (
            <div className="empty">没有匹配的书。</div>
          ) : (
            <div className="book-grid">
              {items.map((b: any) => (
                <BookCard key={b.id} book={b as BookCardData} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
