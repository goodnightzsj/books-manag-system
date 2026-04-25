"use client";
import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { makeProgressSync, type Locator } from "@/lib/progress";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export function PdfReader({
  bookId,
  fileUrl,
  initialPage = 1,
  onLocatorChange,
}: {
  bookId: string;
  fileUrl: string;
  initialPage?: number;
  onLocatorChange?: (l: Locator) => void;
}) {
  const [numPages, setNumPages] = useState<number>(0);
  const [page, setPage] = useState<number>(initialPage);
  const [width, setWidth] = useState<number>(720);
  const sync = useRef(makeProgressSync(bookId));

  useEffect(() => {
    function resize() {
      const w = Math.min(960, Math.max(360, window.innerWidth - 80));
      setWidth(w);
    }
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => {
    if (numPages > 0) {
      const locator: Locator = { type: "pdf", page };
      onLocatorChange?.(locator);
      sync.current.push({
        locator,
        current_page: page,
        total_pages: numPages,
        progress_percent: (page / numPages) * 100,
        status: page >= numPages ? "completed" : "reading",
      });
    }
    return () => sync.current.flushNow();
  }, [page, numPages, onLocatorChange]);

  return (
    <div style={{ display: "grid", gap: 18, justifyItems: "center" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "8px 12px",
          background: "var(--bg-surface)",
          border: "1px solid var(--rule)",
          borderRadius: "var(--radius-md)",
        }}
      >
        <button
          className="btn icon-square"
          aria-label="上一页"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          ←
        </button>
        <span
          className="numeric"
          style={{
            fontFamily: "var(--font-sans)",
            fontFeatureSettings: "'tnum', 'lnum'",
            color: "var(--ink-soft)",
            fontSize: 13,
            minWidth: 64,
            textAlign: "center",
            letterSpacing: "0.04em",
          }}
        >
          {page} / {numPages || "?"}
        </span>
        <button
          className="btn icon-square"
          aria-label="下一页"
          disabled={page >= numPages}
          onClick={() => setPage((p) => Math.min(numPages, p + 1))}
        >
          →
        </button>
      </div>
      <div
        style={{
          boxShadow: "var(--shadow-md)",
          borderRadius: 4,
          background: "#fff",
          border: "1px solid var(--rule)",
        }}
      >
        <Document
          file={fileUrl}
          onLoadSuccess={(doc) => setNumPages(doc.numPages)}
          loading={<div className="empty">加载 PDF 中…</div>}
        >
          <Page pageNumber={page} width={width} />
        </Document>
      </div>
    </div>
  );
}
