"use client";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { api, bookStreamUrl } from "@/lib/api";
import { ReaderDrawer } from "@/components/ReaderDrawer";
import type { Locator } from "@/lib/progress";

const PdfReader = dynamic(() => import("@/components/PdfReader").then((m) => m.PdfReader), {
  ssr: false,
});
const EpubReader = dynamic(() => import("@/components/EpubReader").then((m) => m.EpubReader), {
  ssr: false,
});
const TxtReader = dynamic(() => import("@/components/TxtReader").then((m) => m.TxtReader), {
  ssr: false,
});

export default function ReadPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [book, setBook] = useState<any>(null);
  const [initialLocator, setInitialLocator] = useState<Locator | null>(null);
  const [current, setCurrent] = useState<Locator | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const epubRef = useRef<any>(null);

  useEffect(() => {
    let cancelled = false;
    api.getBook(id).then((b) => !cancelled && setBook(b));
    api.getProgress(id).then(
      (p) => !cancelled && setInitialLocator(p?.locator ?? null),
      () => !cancelled && setInitialLocator(null),
    );
    return () => {
      cancelled = true;
    };
  }, [id]);

  const onLocator = useCallback((l: Locator) => setCurrent(l), []);
  const jumpTo = useCallback(
    (l: Locator) => {
      if (l.type === "epub" && epubRef.current) epubRef.current.goTo(l.cfi);
      // PDF / TXT: set through URL hash isn't easy without remounting; keep UI
      // open so the user can navigate manually. Future work: lift page state.
    },
    [],
  );

  if (!book) return <div className="empty" style={{ marginTop: 80 }}>加载中…</div>;

  const fmt = String(book.file_format).toLowerCase();
  const url = bookStreamUrl(id);

  return (
    <>
      <div className="reader-chrome">
        <Link href="/library" className="btn ghost">← 书架</Link>
        <div style={{ flex: 1, textAlign: "center" }}>
          <div
            style={{
              fontFamily: "var(--font-serif)",
              fontWeight: 600,
              fontSize: 16,
              letterSpacing: "0.01em",
            }}
          >
            {book.title}
          </div>
          <div style={{ fontSize: 12, color: "var(--ink-faint)" }}>
            {book.author ?? "佚名"} · {fmt.toUpperCase()}
          </div>
        </div>
        <button className="btn" onClick={() => setDrawerOpen(true)}>
          ☰ 书签 / 批注
        </button>
      </div>

      <div className={`reader-stage ${fmt}`}>
        {fmt === "pdf" && (
          <PdfReader
            bookId={id}
            fileUrl={url}
            initialPage={initialLocator?.type === "pdf" ? initialLocator.page : 1}
            onLocatorChange={onLocator}
          />
        )}
        {fmt === "epub" && (
          <EpubReader
            ref={epubRef}
            bookId={id}
            fileUrl={url}
            initialCfi={initialLocator?.type === "epub" ? initialLocator.cfi : undefined}
            onLocatorChange={onLocator}
          />
        )}
        {fmt === "txt" && (
          <TxtReader
            bookId={id}
            fileUrl={url}
            initialLine={initialLocator?.type === "txt" ? initialLocator.line : 1}
            onLocatorChange={onLocator}
          />
        )}
        {!["pdf", "epub", "txt"].includes(fmt) && (
          <div className="empty">
            当前格式 <code>{fmt}</code> 暂不支持浏览器阅读，请从管理端下载。
          </div>
        )}
      </div>

      <ReaderDrawer
        bookId={id}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        currentLocator={current}
        onJump={jumpTo}
      />
    </>
  );
}
