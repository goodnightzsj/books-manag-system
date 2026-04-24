"use client";
import { useEffect, useRef, useState } from "react";
import { makeProgressSync, type Locator } from "@/lib/progress";

export function TxtReader({
  bookId,
  fileUrl,
  initialLine = 1,
  onLocatorChange,
}: {
  bookId: string;
  fileUrl: string;
  initialLine?: number;
  onLocatorChange?: (l: Locator) => void;
}) {
  const [lines, setLines] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentLine, setCurrentLine] = useState<number>(initialLine);
  const hostRef = useRef<HTMLPreElement>(null);
  const syncRef = useRef(makeProgressSync(bookId));

  useEffect(() => {
    fetch(fileUrl)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.statusText))))
      .then((text) => setLines(text.split(/\r?\n/)))
      .catch((e) => setError((e as Error).message));
  }, [fileUrl]);

  useEffect(() => {
    function onScroll() {
      if (!hostRef.current || !lines) return;
      const el = hostRef.current;
      const ratio = el.scrollTop / Math.max(1, el.scrollHeight - el.clientHeight);
      const line = Math.max(1, Math.round(ratio * lines.length));
      setCurrentLine(line);
      const locator: Locator = { type: "txt", line };
      onLocatorChange?.(locator);
      syncRef.current.push({
        locator,
        progress_percent: ratio * 100,
        status: ratio >= 0.999 ? "completed" : "reading",
      });
    }
    const el = hostRef.current;
    el?.addEventListener("scroll", onScroll);
    return () => {
      el?.removeEventListener("scroll", onScroll);
      syncRef.current.flushNow();
    };
  }, [lines, onLocatorChange]);

  if (error) return <div className="error">{error}</div>;
  if (!lines) return <div className="empty">加载文本中…</div>;

  return (
    <div>
      <div
        style={{
          fontSize: 12,
          fontFamily: "var(--font-sans)",
          color: "var(--ink-faint)",
          marginBottom: 8,
        }}
      >
        行 {currentLine} / {lines.length}
      </div>
      <pre
        ref={hostRef}
        style={{
          maxHeight: "78vh",
          overflow: "auto",
          whiteSpace: "pre-wrap",
          background: "var(--bg-surface)",
          padding: 28,
          borderRadius: 14,
          border: "1px solid var(--rule)",
          boxShadow: "var(--shadow-sm)",
          fontFamily: "var(--font-serif)",
          fontSize: 17,
          lineHeight: 1.85,
          color: "var(--ink)",
        }}
      >
        {lines.join("\n")}
      </pre>
    </div>
  );
}
