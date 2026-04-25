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

/** Reader theme cycle. Persisted to localStorage. */
type ReaderTheme = "paper" | "sepia" | "dark";
const THEME_KEY = "reader.theme";
const FONT_KEY = "reader.fontSize";
const FONT_STEPS = [14, 15, 16, 17, 18, 20, 22] as const;

type TocItem = { label: string; href: string };

export default function ReadPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [book, setBook] = useState<any>(null);
  const [initialLocator, setInitialLocator] = useState<Locator | null>(null);
  const [current, setCurrent] = useState<Locator | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [tocOpen, setTocOpen] = useState(false);
  const [toc, setToc] = useState<TocItem[]>([]);
  const [theme, setThemeState] = useState<ReaderTheme>("paper");
  const [fontSize, setFontSizeState] = useState<number>(17);
  const epubRef = useRef<any>(null);

  // Theme + font hydrated from localStorage; written to <html data-...>
  // and a CSS variable so EPUB/TXT readers respond without prop drilling.
  useEffect(() => {
    try {
      const t = (localStorage.getItem(THEME_KEY) as ReaderTheme | null) ?? "paper";
      const f = Number(localStorage.getItem(FONT_KEY) ?? "17");
      if (t === "paper" || t === "sepia" || t === "dark") setThemeState(t);
      if (Number.isFinite(f) && f >= 12 && f <= 28) setFontSizeState(f);
    } catch {
      /* SSR / disabled storage — ignore. */
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-reader-theme", theme);
    return () => {
      document.documentElement.removeAttribute("data-reader-theme");
    };
  }, [theme]);

  useEffect(() => {
    document.documentElement.style.setProperty(
      "--reader-font-size",
      `${fontSize}px`,
    );
  }, [fontSize]);

  const setTheme = useCallback((next: ReaderTheme) => {
    setThemeState(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  const setFontSize = useCallback((next: number) => {
    setFontSizeState(next);
    try {
      localStorage.setItem(FONT_KEY, String(next));
    } catch {
      /* ignore */
    }
  }, []);

  function bumpFont(delta: 1 | -1) {
    const idx = FONT_STEPS.findIndex((s) => s === fontSize);
    const here = idx === -1 ? FONT_STEPS.indexOf(17) : idx;
    const nextIdx = Math.min(
      FONT_STEPS.length - 1,
      Math.max(0, here + delta),
    );
    setFontSize(FONT_STEPS[nextIdx]);
  }

  function cycleTheme() {
    setTheme(theme === "paper" ? "sepia" : theme === "sepia" ? "dark" : "paper");
  }

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

  const onToc = useCallback((items: TocItem[]) => setToc(items), []);

  if (!book) return <div className="empty" style={{ marginTop: 80 }}>加载中…</div>;

  const fmt = String(book.file_format).toLowerCase();
  const url = bookStreamUrl(id);
  const isEpub = fmt === "epub";
  const supportsFontSize = isEpub || fmt === "txt";

  const themeIcon = theme === "paper" ? "◐" : theme === "sepia" ? "◑" : "●";
  const themeLabel =
    theme === "paper" ? "纸面" : theme === "sepia" ? "暮色" : "夜读";

  return (
    <>
      <div className="reader-chrome">
        <Link href="/library" className="btn ghost">
          ← 书架
        </Link>
        <div className="chrome-title" style={{ flex: 1, textAlign: "center" }}>
          <div
            style={{
              fontFamily: "var(--font-serif)",
              fontWeight: 600,
              fontSize: 17,
              color: "var(--ink)",
              letterSpacing: "-0.005em",
              fontFeatureSettings: "'tnum', 'lnum', 'kern', 'liga'",
              lineHeight: 1.2,
            }}
          >
            {book.title}
          </div>
          <div
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: 11,
              color: "var(--ink-faint)",
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              marginTop: 3,
              fontWeight: 500,
            }}
          >
            {book.author ?? "佚名"}
            <span aria-hidden style={{ margin: "0 8px", opacity: 0.5 }}>
              ·
            </span>
            {fmt.toUpperCase()}
          </div>
        </div>

        <div className="chrome-group" aria-label="阅读控件">
          {supportsFontSize && (
            <div
              role="group"
              aria-label="字号"
              className="chrome-group"
              style={{ gap: 0 }}
            >
              <button
                className="chrome-btn"
                aria-label="减小字号"
                onClick={() => bumpFont(-1)}
                disabled={fontSize <= FONT_STEPS[0]}
                style={{ borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
              >
                <span className="ch-glyph" style={{ fontSize: 12 }}>
                  A−
                </span>
              </button>
              <button
                className="chrome-btn"
                aria-label="增大字号"
                onClick={() => bumpFont(1)}
                disabled={fontSize >= FONT_STEPS[FONT_STEPS.length - 1]}
                style={{
                  borderLeft: 0,
                  borderTopLeftRadius: 0,
                  borderBottomLeftRadius: 0,
                }}
              >
                <span className="ch-glyph" style={{ fontSize: 14 }}>
                  A+
                </span>
              </button>
            </div>
          )}
          <button
            className="chrome-btn"
            aria-label={`切换主题，当前${themeLabel}`}
            title={`主题：${themeLabel}（点击切换）`}
            onClick={cycleTheme}
          >
            <span aria-hidden>{themeIcon}</span>
            <span style={{ fontSize: 11.5, color: "var(--ink-faint)" }}>
              {themeLabel}
            </span>
          </button>
          {isEpub && (
            <button
              className="chrome-btn"
              aria-label="目录"
              aria-pressed={tocOpen}
              onClick={() => setTocOpen((v) => !v)}
              disabled={toc.length === 0}
              title={toc.length ? `共 ${toc.length} 章` : "目录加载中"}
            >
              目录
            </button>
          )}
          <button className="btn" onClick={() => setDrawerOpen(true)}>
            书签 / 批注
          </button>
        </div>
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
            fontSize={fontSize}
            theme={theme}
            onToc={onToc}
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

      {/* TOC drawer (right side) — only for EPUB */}
      {isEpub && (
        <TocDrawer
          open={tocOpen}
          onClose={() => setTocOpen(false)}
          items={toc}
          onSelect={(href) => {
            epubRef.current?.goTo(href);
            setTocOpen(false);
          }}
        />
      )}

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

/**
 * Lightweight side drawer for the EPUB table of contents. Mirrors the
 * styling of `ReaderDrawer` (paper surface, hairline border, terracotta
 * focus) but without the bookmark/annotation tabs.
 */
function TocDrawer({
  open,
  onClose,
  items,
  onSelect,
}: {
  open: boolean;
  onClose: () => void;
  items: TocItem[];
  onSelect: (href: string) => void;
}) {
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
          width: "min(360px, 90vw)",
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
            padding: "18px 22px 14px",
            borderBottom: "1px solid var(--rule)",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div style={{ flex: 1 }}>
            <div className="eyebrow">章节目录</div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 18,
                fontWeight: 600,
                marginTop: 2,
                color: "var(--ink)",
                letterSpacing: "-0.005em",
              }}
            >
              共 <span className="numeric">{items.length}</span> 章
            </div>
          </div>
          <button className="btn ghost" onClick={onClose} aria-label="关闭">
            ✕
          </button>
        </div>
        <div style={{ overflowY: "auto", padding: "8px 6px 24px", flex: 1 }}>
          {items.length === 0 ? (
            <div className="empty">本书未提供目录信息。</div>
          ) : (
            items.map((it, i) => (
              <button
                key={`${it.href}-${i}`}
                onClick={() => onSelect(it.href)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  border: 0,
                  background: "transparent",
                  padding: "10px 16px",
                  fontFamily: "var(--font-serif)",
                  fontSize: 14,
                  color: "var(--ink)",
                  cursor: "pointer",
                  borderLeft: "1px solid transparent",
                  transition: "border-color 160ms ease, background 160ms ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderLeftColor = "var(--accent)";
                  e.currentTarget.style.background = "var(--bg-muted)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderLeftColor = "transparent";
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <span
                  className="numeric"
                  style={{
                    color: "var(--ink-faint)",
                    marginRight: 10,
                    fontFamily: "var(--font-sans)",
                    fontSize: 11,
                    letterSpacing: "0.04em",
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                {it.label}
              </button>
            ))
          )}
        </div>
      </aside>
    </>
  );
}
