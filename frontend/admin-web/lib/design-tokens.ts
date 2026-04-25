/**
 * Editorial Library Archive — design tokens.
 *
 * One vocabulary shared between admin-web and reader-web.
 * Admin-web is the *cooler*, denser sibling: smaller controls, tighter
 * line-height, slightly cooler paper. Reader-web keeps the warm paper.
 *
 * Tokens are exported as plain string constants so they can be embedded in
 * inline `style` attributes (CSS variables remain the source of truth in
 * `globals.css`; this file just gives TypeScript-side parity).
 */

export const ink = {
  /** Primary text — near-black with a hint of warmth. */
  base: "#18181B",
  /** Secondary text. */
  soft: "#57534E",
  /** Helper / metadata. */
  faint: "#78716C",
  /** Inverted text on dark surfaces. */
  inverse: "#F5F4EE",
} as const;

export const paper = {
  /** Reader background — warm paper. */
  warm: "#FBF7EE",
  /** Admin background — cooler, office-grade beige. */
  cool: "#F5F4EE",
  /** Card / surface base. */
  surface: "#FFFFFF",
  /** Quiet inset surface (table headers, muted blocks). */
  muted: "#EFEBDF",
  /** Hairline rules and subtle borders. */
  rule: "#E7E2D6",
  /** Sider / dark navigation. */
  ink: "#1B1A17",
  /** Slightly lighter ink for hover lanes inside the sider. */
  inkHover: "#26241F",
} as const;

export const accent = {
  /** Terracotta — primary brand accent (book-spine red). */
  base: "#B4502A",
  /** Lighter terracotta wash for focus rings, soft surfaces. */
  soft: "#F2DCCC",
  /** Slightly darker, used for active / pressed buttons. */
  deep: "#8F3E1F",
} as const;

export const semantic = {
  /** Forest green — hash done, completed jobs. */
  ok: "#2F6B4A",
  okSoft: "#DDEBE0",
  /** Brass / warning. */
  warn: "#B8862D",
  warnSoft: "#F3E5C2",
  /** Deep red — destructive / failed. */
  danger: "#9B2C2C",
  dangerSoft: "#F2D6D6",
  /** Quiet info — slate, never blue. */
  info: "#4B5563",
  infoSoft: "#E5E7EB",
} as const;

/**
 * Spacing scale — multiples of 4. Keeping it small intentionally;
 * no mid-values, no "magic" 14/22 numbers.
 */
export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 40,
} as const;

/** Border radius scale — restrained for archive feel. */
export const radius = {
  sm: 4,
  md: 6,
  lg: 10,
  pill: 999,
} as const;

export const fontStack = {
  sans:
    "Inter, 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
  serif:
    "'Source Serif 4', 'Source Serif Pro', 'Noto Serif SC', 'Source Han Serif SC', Georgia, 'Times New Roman', serif",
  mono:
    "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace",
} as const;

/**
 * Aggregated CSS variable definitions. Mirrored in `globals.css` for runtime
 * but exported here so non-CSS code paths can read the same source of truth.
 */
export const cssVars = {
  "--ink": ink.base,
  "--ink-soft": ink.soft,
  "--ink-faint": ink.faint,
  "--paper": paper.warm,
  "--paper-cool": paper.cool,
  "--surface": paper.surface,
  "--rule": paper.rule,
  "--accent": accent.base,
  "--accent-soft": accent.soft,
  "--accent-deep": accent.deep,
  "--ok": semantic.ok,
  "--warn": semantic.warn,
  "--danger": semantic.danger,
} as const;
