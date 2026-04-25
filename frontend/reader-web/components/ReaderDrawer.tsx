"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Locator } from "@/lib/progress";
import { ErrorBanner } from "./ErrorBanner";

type Bookmark = {
  id: string;
  locator: Locator;
  title: string | null;
  note: string | null;
  created_at: string;
};

type Annotation = {
  id: string;
  locator_start: Locator;
  locator_end?: Locator | null;
  highlight_text?: string | null;
  note?: string | null;
  color?: string | null;
  created_at: string;
};

type Tab = "bookmarks" | "annotations";

function formatLocator(l: Locator): string {
  if (l.type === "pdf") return `页 ${l.page}`;
  if (l.type === "epub")
    return l.chapter ? `${l.chapter}` : `${(l.progression ?? 0) * 100 | 0}%`;
  if (l.type === "txt") return `行 ${l.line}`;
  return "位置";
}

export function ReaderDrawer({
  bookId,
  open,
  onClose,
  currentLocator,
  onJump,
}: {
  bookId: string;
  open: boolean;
  onClose: () => void;
  currentLocator: Locator | null;
  onJump?: (locator: Locator) => void;
}) {
  const [tab, setTab] = useState<Tab>("bookmarks");
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [bm, an] = await Promise.all([
        api.listBookmarks(bookId).catch(() => ({ items: [], total: 0 })),
        api.listAnnotations(bookId).catch(() => ({ items: [], total: 0 })),
      ]);
      setBookmarks(bm.items as Bookmark[]);
      setAnnotations(an.items as Annotation[]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  async function addBookmark() {
    if (!currentLocator) {
      setError("无法获取当前位置");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.createBookmark(bookId, {
        locator: currentLocator,
        title: title.trim() || null,
        note: note.trim() || null,
      });
      setTitle("");
      setNote("");
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function removeBookmark(id: string) {
    try {
      await api.deleteBookmark(bookId, id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function removeAnnotation(id: string) {
    try {
      await api.deleteAnnotation(bookId, id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(15,14,12,0.35)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
          transition: "opacity 200ms ease",
          zIndex: 50,
        }}
      />
      <aside
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          height: "100vh",
          width: "min(420px, 92vw)",
          background: "var(--bg-surface)",
          borderLeft: "1px solid var(--rule)",
          boxShadow: "var(--shadow-lg)",
          transform: `translateX(${open ? 0 : 100}%)`,
          transition: "transform 240ms cubic-bezier(0.2,0.8,0.2,1)",
          zIndex: 60,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "18px 22px 14px",
            borderBottom: "1px solid var(--rule)",
            gap: 12,
          }}
        >
          <div style={{ flex: 1 }}>
            <div className="eyebrow">阅读侧边栏</div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 18,
                fontWeight: 600,
                color: "var(--ink)",
                marginTop: 2,
                letterSpacing: "-0.005em",
              }}
            >
              {tab === "bookmarks" ? "书签" : "批注"}
            </div>
          </div>
          <button className="btn ghost" onClick={onClose} aria-label="关闭">
            ✕
          </button>
        </div>
        <div style={{ padding: "12px 22px", borderBottom: "1px solid var(--rule)" }}>
          <div className="segmented" role="tablist">
            <button
              role="tab"
              aria-selected={tab === "bookmarks"}
              className={tab === "bookmarks" ? "active" : ""}
              onClick={() => setTab("bookmarks")}
            >
              书签 <span className="numeric">({bookmarks.length})</span>
            </button>
            <button
              role="tab"
              aria-selected={tab === "annotations"}
              className={tab === "annotations" ? "active" : ""}
              onClick={() => setTab("annotations")}
            >
              批注 <span className="numeric">({annotations.length})</span>
            </button>
          </div>
        </div>

        {error && (
          <div style={{ margin: 16 }}>
            <ErrorBanner
              title="操作失败"
              description={error}
              onRetry={() => setError(null)}
              retryLabel="清除"
            />
          </div>
        )}

        <div style={{ overflowY: "auto", padding: "14px 22px", flex: 1 }}>
          {tab === "bookmarks" && (
            <>
              <div
                className="card"
                style={{ padding: 14, marginBottom: 16, background: "var(--bg-muted)" }}
              >
                <div className="eyebrow">在此处添加书签</div>
                <div style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>
                  当前位置：
                  {currentLocator ? formatLocator(currentLocator) : "未知"}
                </div>
                <input
                  className="input"
                  placeholder="标题（可选）"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{ marginTop: 10 }}
                />
                <textarea
                  className="input"
                  placeholder="备注（可选）"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={3}
                  style={{ marginTop: 8, resize: "vertical", fontFamily: "inherit" }}
                />
                <button
                  className="btn primary"
                  disabled={busy || !currentLocator}
                  onClick={addBookmark}
                  style={{ marginTop: 10, width: "100%", justifyContent: "center" }}
                >
                  {busy ? "保存中…" : "添加书签"}
                </button>
              </div>

              {loading ? (
                <div className="empty">加载中…</div>
              ) : bookmarks.length === 0 ? (
                <div className="empty">还没有书签。</div>
              ) : (
                bookmarks.map((b) => (
                  <div
                    key={b.id}
                    className="card"
                    style={{ padding: 14, marginBottom: 12 }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "baseline",
                        justifyContent: "space-between",
                      }}
                    >
                      <strong style={{ fontFamily: "var(--font-serif)" }}>
                        {b.title || "未命名书签"}
                      </strong>
                      <span
                        style={{
                          fontSize: 11,
                          fontFamily: "var(--font-sans)",
                          color: "var(--ink-faint)",
                          letterSpacing: "0.04em",
                        }}
                      >
                        {formatLocator(b.locator)}
                      </span>
                    </div>
                    {b.note && (
                      <p style={{ fontSize: 14, marginTop: 6, color: "var(--ink-soft)" }}>
                        {b.note}
                      </p>
                    )}
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        marginTop: 10,
                        justifyContent: "flex-end",
                      }}
                    >
                      {onJump && (
                        <button className="btn" onClick={() => onJump(b.locator)}>
                          跳转
                        </button>
                      )}
                      <button className="btn" onClick={() => removeBookmark(b.id)}>
                        删除
                      </button>
                    </div>
                  </div>
                ))
              )}
            </>
          )}

          {tab === "annotations" && (
            <>
              {loading ? (
                <div className="empty">加载中…</div>
              ) : annotations.length === 0 ? (
                <div className="empty">
                  选中文字后在阅读器内加高亮，它们会出现在这里。
                </div>
              ) : (
                annotations.map((a) => (
                  <div
                    key={a.id}
                    className="card"
                    style={{
                      padding: 14,
                      marginBottom: 12,
                      borderLeft: `3px solid ${a.color ?? "var(--accent)"}`,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 11,
                        fontFamily: "var(--font-sans)",
                        color: "var(--ink-faint)",
                        letterSpacing: "0.04em",
                      }}
                    >
                      {formatLocator(a.locator_start)}
                    </div>
                    {a.highlight_text && (
                      <blockquote
                        style={{
                          margin: "6px 0",
                          padding: "6px 12px",
                          background: "var(--bg-muted)",
                          borderRadius: 4,
                          fontStyle: "italic",
                        }}
                      >
                        {`“${a.highlight_text}”`}
                      </blockquote>
                    )}
                    {a.note && (
                      <p style={{ fontSize: 14, color: "var(--ink-soft)" }}>{a.note}</p>
                    )}
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        marginTop: 10,
                        justifyContent: "flex-end",
                      }}
                    >
                      {onJump && (
                        <button className="btn" onClick={() => onJump(a.locator_start)}>
                          跳转
                        </button>
                      )}
                      <button className="btn" onClick={() => removeAnnotation(a.id)}>
                        删除
                      </button>
                    </div>
                  </div>
                ))
              )}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
