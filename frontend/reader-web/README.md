# Books Reader Web

Next.js 14 + TypeScript reader shell covering PDF (pdf.js via react-pdf),
EPUB (epub.js) and TXT.

## Dev

```bash
cp .env.example .env.local
pnpm install
pnpm dev      # http://localhost:3001
```

Sign in via `/login`; then `/library` shows recent reads and `/search`
finds books. Clicking a book opens `/read/[id]` which streams the file
via `/api/v1/files/stream/{book_id}` and syncs progress through
`PUT /api/v1/reading-progress/{book_id}`.

## Progress locator

See `lib/progress.ts` -- it debounces updates (default 1.2 s) and
produces locator payloads matching the backend schema:

- PDF:  `{ type: "pdf", page }`
- EPUB: `{ type: "epub", cfi, progression }`
- TXT:  `{ type: "txt", line }`
