"use client";
import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { makeProgressSync, type Locator } from "@/lib/progress";

// The worker file is copied into /public/ by the `prebuild` script (see
// package.json). Loading it from a static URL avoids Next.js / webpack
// trying to re-parse the prebundled ESM worker, which fails because it
// uses top-level import/export inside a string.
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

const ZOOM_STEPS = [320, 520, 720, 960] as const;
type ZoomStep = (typeof ZOOM_STEPS)[number];

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
  const [zoomIdx, setZoomIdx] = useState<number>(2); // start at 720
  const [maxWidth, setMaxWidth] = useState<number>(960);
  const [editingPage, setEditingPage] = useState(false);
  const [pageDraft, setPageDraft] = useState<string>(String(initialPage));
  const sync = useRef(makeProgressSync(bookId));

  useEffect(() => {
    function resize() {
      // Cap zoom width to viewport - 80px so zoom doesn't overflow.
      setMaxWidth(Math.max(280, window.innerWidth - 80));
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

  const width: ZoomStep = ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, zoomIdx))];
  const renderWidth = Math.min(width, maxWidth);

  function commitPage(raw: string) {
    const n = Math.round(Number(raw));
    if (Number.isFinite(n) && n >= 1 && n <= (numPages || n)) {
      setPage(n);
    }
    setPageDraft(String(page));
    setEditingPage(false);
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 18,
        width: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
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
        {editingPage ? (
          <input
            className="page-input"
            autoFocus
            type="number"
            min={1}
            max={numPages || undefined}
            value={pageDraft}
            onChange={(e) => setPageDraft(e.target.value)}
            onBlur={(e) => commitPage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitPage((e.target as HTMLInputElement).value);
              if (e.key === "Escape") {
                setPageDraft(String(page));
                setEditingPage(false);
              }
            }}
          />
        ) : (
          <button
            type="button"
            onClick={() => {
              setPageDraft(String(page));
              setEditingPage(true);
            }}
            aria-label="跳转到指定页"
            title="点击输入页码"
            className="numeric"
            style={{
              border: "1px dashed transparent",
              background: "transparent",
              cursor: "text",
              fontFamily: "var(--font-sans)",
              fontFeatureSettings: "'tnum', 'lnum'",
              color: "var(--ink-soft)",
              fontSize: 13,
              minWidth: 72,
              padding: "2px 6px",
              borderRadius: 4,
              letterSpacing: "0.04em",
              transition: "border-color 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--rule)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "transparent";
            }}
          >
            {page} / {numPages || "?"}
          </button>
        )}
        <button
          className="btn icon-square"
          aria-label="下一页"
          disabled={page >= numPages}
          onClick={() => setPage((p) => Math.min(numPages, p + 1))}
        >
          →
        </button>
        <span
          aria-hidden
          style={{ width: 1, height: 22, background: "var(--rule)", margin: "0 4px" }}
        />
        <button
          className="btn icon-square"
          aria-label="缩小"
          onClick={() => setZoomIdx((i) => Math.max(0, i - 1))}
          disabled={zoomIdx <= 0}
        >
          −
        </button>
        <span
          className="numeric"
          style={{
            color: "var(--ink-faint)",
            fontSize: 11,
            fontFamily: "var(--font-sans)",
            letterSpacing: "0.06em",
            minWidth: 42,
            textAlign: "center",
            textTransform: "uppercase",
          }}
        >
          {width}px
        </span>
        <button
          className="btn icon-square"
          aria-label="放大"
          onClick={() => setZoomIdx((i) => Math.min(ZOOM_STEPS.length - 1, i + 1))}
          disabled={zoomIdx >= ZOOM_STEPS.length - 1}
        >
          ＋
        </button>
      </div>
      <div
        style={{
          boxShadow: "var(--shadow-md)",
          borderRadius: 4,
          background: "#fff",
          border: "1px solid var(--rule)",
          maxWidth: "100%",
        }}
      >
        <Document
          file={fileUrl}
          onLoadSuccess={(doc) => setNumPages(doc.numPages)}
          loading={<div className="empty">加载 PDF 中…</div>}
        >
          <Page pageNumber={page} width={renderWidth} />
        </Document>
      </div>
    </div>
  );
}
