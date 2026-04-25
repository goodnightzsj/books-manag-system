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
          "'Source Serif 4', 'Source Serif Pro', 'Noto Serif SC', 'Source Han Serif SC', Georgia, serif !important",
        "font-size": "17px !important",
        "line-height": "1.85 !important",
        color: "var(--ink) !important",
        padding: "0 16px !important",
      },
      p: {
        margin: "0 0 0.9em 0 !important",
        "text-align": "justify !important",
        "text-indent": "1.5em !important",
      },
      "p:first-of-type": {
        "text-indent": "0 !important",
      },
      h1: {
        "font-weight": "600 !important",
        "letter-spacing": "-0.012em !important",
        "margin-top": "1.4em !important",
      },
      h2: {
        "font-weight": "600 !important",
        "letter-spacing": "-0.008em !important",
        "margin-top": "1.2em !important",
      },
      blockquote: {
        "border-left": "2px solid var(--accent) !important",
        "padding-left": "1em !important",
        "font-style": "italic !important",
        color: "var(--ink-soft) !important",
      },
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
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--rule)",
          boxShadow: "var(--shadow-sm)",
          padding: 20,
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 16,
          marginTop: 18,
        }}
      >
        <button
          className="btn icon-square"
          aria-label="上一页"
          onClick={() => renditionRef.current?.prev()}
        >
          ←
        </button>
        <button
          className="btn icon-square"
          aria-label="下一页"
          onClick={() => renditionRef.current?.next()}
        >
          →
        </button>
      </div>
    </div>
  );
});
