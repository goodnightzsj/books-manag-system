"use client";
import { useEffect, useImperativeHandle, useRef, forwardRef } from "react";
import ePub, { type Rendition } from "epubjs";
import { makeProgressSync, type Locator } from "@/lib/progress";

export type EpubHandle = {
  goTo: (target: string) => void;
  prev: () => void;
  next: () => void;
};

type ReaderTheme = "paper" | "sepia" | "dark";

type TocItem = { label: string; href: string };

const THEME_PALETTE: Record<ReaderTheme, { bg: string; ink: string; rule: string }> = {
  paper: { bg: "#FBF7EE", ink: "#18181B", rule: "#E7E2D6" },
  sepia: { bg: "#F1E4CC", ink: "#3B2F22", rule: "#D9C7AA" },
  dark: { bg: "#16140F", ink: "#E8E0CC", rule: "#36312A" },
};

export const EpubReader = forwardRef<
  EpubHandle,
  {
    bookId: string;
    fileUrl: string;
    initialCfi?: string;
    onLocatorChange?: (l: Locator) => void;
    fontSize?: number;
    theme?: ReaderTheme;
    onToc?: (items: TocItem[]) => void;
  }
>(function EpubReader(
  {
    bookId,
    fileUrl,
    initialCfi,
    onLocatorChange,
    fontSize = 17,
    theme = "paper",
    onToc,
  },
  ref,
) {
  const hostRef = useRef<HTMLDivElement>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const syncRef = useRef(makeProgressSync(bookId));

  useImperativeHandle(
    ref,
    () => ({
      // Accept either a CFI or a chapter href — epub.js handles both.
      goTo: (target) => renditionRef.current?.display(target),
      prev: () => renditionRef.current?.prev(),
      next: () => renditionRef.current?.next(),
    }),
    [],
  );

  // Effect 1: mount epub once per fileUrl. Theme/font are applied via
  // separate effects so toggling them doesn't tear down the rendition.
  useEffect(() => {
    if (!hostRef.current) return;
    const book = ePub(fileUrl);
    const rendition = book.renderTo(hostRef.current, {
      width: "100%",
      height: "78vh",
      spread: "none",
    });

    renditionRef.current = rendition;
    rendition.display(initialCfi ?? undefined);

    // Push TOC up so the parent can render a chapter drawer.
    book.loaded.navigation.then((nav) => {
      try {
        const flatten = (
          nodes: Array<{ label?: string; href: string; subitems?: any[] }>,
        ): TocItem[] => {
          const out: TocItem[] = [];
          for (const n of nodes) {
            const label = (n.label ?? "").trim() || n.href;
            out.push({ label, href: n.href });
            if (n.subitems && n.subitems.length > 0) {
              out.push(...flatten(n.subitems));
            }
          }
          return out;
        };
        onToc?.(flatten(nav.toc as any));
      } catch {
        onToc?.([]);
      }
    });

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
      renditionRef.current = null;
    };
  }, [fileUrl, initialCfi, onLocatorChange, onToc]);

  // Effect 2: keep theme + font in sync. Re-registers the named theme each
  // time so we can avoid creating an ever-growing list of themes.
  useEffect(() => {
    const r = renditionRef.current;
    if (!r) return;
    const palette = THEME_PALETTE[theme];
    // epub.js requires distinct theme names; we re-register and re-select.
    const name = `editorial-${theme}-${fontSize}`;
    try {
      r.themes.register(name, {
        body: {
          background: `${palette.bg} !important`,
          color: `${palette.ink} !important`,
          "font-family":
            "'Source Serif 4', 'Source Serif Pro', 'Noto Serif SC', 'Source Han Serif SC', Georgia, serif !important",
          "line-height": "1.85 !important",
          padding: "0 16px !important",
        },
        p: {
          margin: "0 0 0.85em 0 !important",
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
          color: `${palette.ink} !important`,
        },
        h2: {
          "font-weight": "600 !important",
          "letter-spacing": "-0.008em !important",
          "margin-top": "1.2em !important",
          color: `${palette.ink} !important`,
        },
        blockquote: {
          "border-left": "2px solid #B4502A !important",
          "padding-left": "1em !important",
          "font-style": "italic !important",
          color:
            theme === "dark"
              ? "#B5AC97 !important"
              : theme === "sepia"
              ? "#6B5A47 !important"
              : "#57534E !important",
        },
        a: { color: "#B4502A !important" },
      });
      r.themes.select(name);
      r.themes.fontSize(`${fontSize}px`);
    } catch {
      /* rendition not yet ready — ignore */
    }
  }, [theme, fontSize]);

  return (
    <div>
      <div
        ref={hostRef}
        className="epub-host"
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
