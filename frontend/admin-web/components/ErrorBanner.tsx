"use client";
import { Button } from "antd";
import type { ReactNode } from "react";

/**
 * Editorial error banner used across admin pages instead of AntD's red
 * `Alert`. A 1px terracotta strip on the left, serif title, sans
 * description, optional retry. Quieter than `<Alert type="error">` and
 * matches the archive aesthetic.
 */
export function ErrorBanner({
  title = "请求失败",
  description,
  onRetry,
  retryLabel = "重试",
  style,
}: {
  title?: ReactNode;
  description?: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      role="alert"
      style={{
        position: "relative",
        background: "var(--surface)",
        border: "1px solid var(--rule)",
        borderRadius: 6,
        padding: "14px 18px 14px 22px",
        display: "grid",
        gap: 6,
        ...style,
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
      {onRetry && (
        <div>
          <Button size="small" onClick={onRetry} style={{ marginTop: 4 }}>
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
