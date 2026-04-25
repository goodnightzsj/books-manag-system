"use client";
import type { ReactNode } from "react";

/**
 * Editorial error banner — paper-colored card with a 1px terracotta strip
 * down the left edge, a serif title and a sans subtitle. Replaces ad-hoc
 * `<div className="error">` blocks scattered through the reader.
 *
 * The strip is purely visual: severity is communicated by the title +
 * description pair, never by a screaming red background. Reading is the
 * primary task here, so even errors stay quiet.
 */
export function ErrorBanner({
  title = "出了点状况",
  description,
  onRetry,
  retryLabel = "重试",
  children,
}: {
  title?: ReactNode;
  description?: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  children?: ReactNode;
}) {
  return (
    <div
      role="alert"
      className="error-banner"
      style={{
        position: "relative",
        background: "var(--bg-surface)",
        border: "1px solid var(--rule)",
        borderRadius: "var(--radius-md)",
        padding: "14px 18px 14px 22px",
        display: "grid",
        gap: 4,
      }}
    >
      <span
        aria-hidden
        style={{
          position: "absolute",
          left: 0,
          top: 8,
          bottom: 8,
          width: 1,
          background: "var(--accent)",
        }}
      />
      <div
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: 15,
          fontWeight: 600,
          color: "var(--ink)",
          letterSpacing: "-0.005em",
        }}
      >
        {title}
      </div>
      {description && (
        <div
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 12.5,
            color: "var(--ink-soft)",
            lineHeight: 1.55,
          }}
        >
          {description}
        </div>
      )}
      {children}
      {onRetry && (
        <div style={{ marginTop: 8 }}>
          <button className="btn" onClick={onRetry}>
            {retryLabel}
          </button>
        </div>
      )}
    </div>
  );
}
