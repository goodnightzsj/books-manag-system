# Books Admin Web

Next.js 14 (App Router) + TypeScript admin console for the Books
Management System backend.

## Dev

```bash
cp .env.example .env.local
pnpm install   # or npm install / yarn
pnpm dev       # http://localhost:3000
```

The dev server proxies `/api/*` to `NEXT_PUBLIC_API_BASE` (defaults to
`http://localhost:8000`), so CORS is not required for local development.

## Pages

- `/login` -- admin credentials -> stores bearer token in `localStorage`.
- `/books` -- search / list / edit / delete books.
- `/books/[id]` -- detail + metadata/cover re-sync actions.
- `/scanner` -- directory scan form + job list.
- `/scanner/jobs/[id]` -- job detail with item-level status.
- `/categories` -- CRUD.
