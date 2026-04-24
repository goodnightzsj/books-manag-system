"use client";
import { useEffect, useImperativeHandle, useRef, forwardRef } from "react";
import ePub, { type Rendition } from "epubjs";
import { makeProgressSync, type Locator } from "@/lib/progress";

export type EpubHandle = {
  goTo: (cfi: string) => void;
  prev: () => void;
  next: () => void;
};

export const EpubReader = forwardRef<
  EpubHandle,
  {
    bookId: string;
    fileUrl: string;
    initialCfi?: string;
    onLocatorChange?: (l: Locator) => void;
  }
>(function EpubReader({ bookId, fileUrl, initialCfi, onLocatorChange }, ref) {
  const hostRef = useRef<HTMLDivElement>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const syncRef = useRef(makeProgressSync(bookId));

  useImperativeHandle(
    ref,
    () => ({
      goTo: (cfi) => renditionRef.current?.display(cfi),
      prev: () => renditionRef.current?.prev(),
      next: () => renditionRef.current?.next(),
    }),
    [],
  );

  useEffect(() => {
    if (!hostRef.current) return;
    const book = ePub(fileUrl);
    const rendition = book.renderTo(hostRef.current, {
      width: "100%",
      height: "78vh",
      spread: "none",
    });
    rendition.themes.default({
      body: {
        "font-family":
          "'Noto Serif SC', 'Source Han Serif SC', Georgia, serif !important",
        "line-height": "1.75 !important",
        color: "var(--ink) !important",
        padding: "0 12px !important",
      },
      p: { margin: "0 0 1em 0 !important" },
    });
    renditionRef.current = rendition;
    rendition.display(initialCfi ?? undefined);

    const onRelocated = (loc: any) => {
      const cfi = loc?.start?.cfi as string | undefined;
      const progression =
        typeof loc?.start?.percentage === "number" ? loc.start.percentage : undefined;
      const chapter = loc?.start?.href as string | undefined;
      if (cfi) {
        const locator: Locator = { type: "epub", cfi, progression, chapter };
        onLocatorChange?.(locator);
        syncRef.current.push({
          locator,
          progress_percent:
            typeof progression === "number" ? progression * 100 : undefined,
        });
      }
    };
    rendition.on("relocated", onRelocated);

    return () => {
      syncRef.current.flushNow();
      rendition.destroy();
    };
  }, [fileUrl, initialCfi, onLocatorChange]);

  return (
    <div>
      <div
        ref={hostRef}
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--rule)",
          boxShadow: "var(--shadow-sm)",
          padding: 16,
        }}
      />
      <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 14 }}>
        <button className="btn" onClick={() => renditionRef.current?.prev()}>
          ← 上一页
        </button>
        <button className="btn" onClick={() => renditionRef.current?.next()}>
          下一页 →
        </button>
      </div>
    </div>
  );
});
