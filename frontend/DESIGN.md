# Frontend Design — Editorial Library Archive

One-page reference for `frontend/admin-web` and `frontend/reader-web`.
Both apps share the same design vocabulary; admin-web is the cooler / denser
sibling.

## Theme

**Editorial Library Archive.** Inspirations: leather book spines, paper card
catalogs, independent bookshop signage. No glassmorphism, no gradient buttons,
no AI-template indigo. Anchor accent is **terracotta** (`#B4502A`) — the
canonical book-spine red.

## Color tokens

```
--ink         #18181B   primary text (warm near-black)
--ink-soft    #57534E   secondary text
--ink-faint   #78716C   tertiary / metadata

--paper       #FBF7EE   reader-web background (warm)
--paper-cool  #F5F4EE   admin-web background (cooler office)
--surface     #FFFFFF   cards / inputs
--muted       #EFEBDF   table headers, soft inset
--rule        #E7E2D6   1px hairlines

--accent      #B4502A   terracotta — primary
--accent-soft #F2DCCC   focus rings, soft surfaces
--accent-deep #8F3E1F   active / pressed buttons

--ok          #2F6B4A   forest green (hash done, completed)
--warn        #B8862D   brass
--danger      #9B2C2C   deep red
--info        #4B5563   slate (never blue)
```

CSS variables live in:
- `frontend/admin-web/app/globals.css`
- `frontend/reader-web/app/globals.css`

TypeScript parity (admin only): `frontend/admin-web/lib/design-tokens.ts`.

AntD `ThemeConfig` consumes these tokens via
`frontend/admin-web/lib/theme.ts`.

## Type stack

```
sans   Inter, "Noto Sans SC", -apple-system, ...
serif  "Source Serif 4", "Source Serif Pro", "Noto Serif SC",
       "Source Han Serif SC", Georgia, serif
mono   "JetBrains Mono", ui-monospace, ...
```

Roles:
- **admin-web**: sans for body, serif accent for h1 + book titles + brand
  lockup `books.`.
- **reader-web**: serif everywhere except UI chrome (nav, eyebrows, metadata).

OpenType:
- `cv11`, `ss01`, `cv09` on Inter to soften geometric letters.
- `tnum`, `lnum` on `.numeric` for tabular figures (counts, time, IDs).
- `kern`, `liga`, `calt` on serif body for proper kerning + ligatures.

## Spacing scale

`4 / 8 / 12 / 16 / 24 / 40 px`. No mid-values. Anything else is a smell.

```
xs   4    inline icon offset
sm   8    button gap, tag padding
md   12   row padding, related controls
lg   16   between cards / form rows
xl   24   between sections
xxl  40   page top padding, hero spacing
```

Admin uses tighter rhythm: 14/20 row paddings, 56px header.
Reader is more generous: 24/28 page padding, 64-96px section gaps.

## Radius scale

`4 / 6 / 10 / 999 px`. Most elements use **6**. Cards use **10**. No 14/16.

## Anti-AI rules (must)

1. **No purple/violet/indigo/pink anywhere.** Default AntD `success/warning`
   tag colors are bypassed via local `.tag-ok / .tag-warn / .tag-danger /
   .tag-quiet / .tag-accent` utility classes.
2. **No gradient buttons.** Primary is solid `--accent`, hover is solid
   `--accent-deep`.
3. **No glassmorphism.** Cards have a 1px hairline border + zero or
   minimal shadow.
4. **No "AI bounce" hover.** `book-card` rises 1px and darkens its border.
   List rows shift 1px right and grow a left accent rule.
5. **No emoji as brand.** The brand lockup is serif lowercase `books.` with
   the period in terracotta. Emoji only allowed in low-stakes microcopy
   (none currently).
6. **Visible focus.** Inputs / buttons gain a 2px terracotta outline, never
   the default browser blue ring.
7. **Tables.** No zebra striping. Header is muted paper, rows are separated
   by 1px `--rule`, column dividers are removed.

## Key components

| Component | Path |
|-----------|------|
| AntD theme | `admin-web/lib/theme.ts` |
| Design tokens (TS) | `admin-web/lib/design-tokens.ts` |
| App shell + brand lockup + breadcrumbs | `admin-web/components/AppShell.tsx` |
| Editorial CSS utilities | `admin-web/app/globals.css` (`.eyebrow`, `.numeric`, `.list-row`, `.tag-*`, `.empty-state`) |
| Reader brand lockup | `reader-web/components/TopBar.tsx` |
| BookCard (warm cover, no pill rating) | `reader-web/components/BookCard.tsx` |
| Segmented control | `reader-web/app/globals.css` (`.segmented`) |

## Maintainer notes

- When adding a new color, **first** check whether one of the existing tokens
  fits. Adding mid-saturation hues will dilute the palette.
- Status / state colors must always come from `ok / warn / danger / info`,
  never from raw AntD tag colors (those skew blue/purple).
- Heading 1 in `reader-web` has a decorative left rule via `h1::before` —
  preserve the 16px left padding when adding new pages.
- Keep ALL hover states subtle: 1px transform max, no glow, no scale > 1.02.
- Keep ALL `transition` durations between 150ms and 240ms. Anything longer
  reads as "AI demo".
