import type { CSSProperties } from "react";

/**
 * Books mark — three book spines, middle one in terracotta. Pairs with
 * the wordmark `books.` typeset in serif. Inert SVG (no <Link>): the
 * caller decides where it goes. Supports `size` and `tone` ("paper" for
 * light surfaces, "ink" for dark sider).
 */
export function BrandMark({
  size = 28,
  tone = "paper",
  style,
}: {
  size?: number;
  tone?: "paper" | "ink";
  style?: CSSProperties;
}) {
  const bg = tone === "ink" ? "transparent" : "#FBF7EE";
  const top = tone === "ink" ? "#C9C2B0" : "#2F2A23";
  const bottom = tone === "ink" ? "#9C9484" : "#3A332C";
  const accent = "#B4502A";
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      width={size}
      height={size}
      style={style}
      aria-label="books"
      role="img"
      fill="none"
    >
      <rect width="64" height="64" rx="12" fill={bg} />
      <rect x="11" y="14" width="38" height="10" rx="1.5" fill={top} />
      <rect x="9" y="27" width="42" height="10" rx="1.5" fill={accent} />
      <rect x="13" y="40" width="38" height="10" rx="1.5" fill={bottom} />
    </svg>
  );
}
