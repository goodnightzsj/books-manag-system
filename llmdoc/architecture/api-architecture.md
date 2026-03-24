# API Architecture

## 1. Identity

- **What it is:** The FastAPI REST layer under `/api/v1`.
- **Purpose:** Expose authentication, catalog, scanner jobs, file access, and recommendation functionality with shared auth dependencies and a small RBAC split.

## 2. Core Components

- `backend/app/main.py:6-27` -- Creates the FastAPI app, configures CORS, and mounts the API router.
- `backend/app/api/router.py:1-14` -- Aggregates all eight routers.
- `backend/app/api/deps.py:11-40` -- Shared `get_current_user` and `require_admin` dependencies.
- `backend/app/api/auth.py:10-61` -- Registration, login, and current-user lookup.
- `backend/app/api/books.py:17-118` -- Search-backed book list/detail plus admin-only create, update, and delete.
- `backend/app/api/categories.py:12-164` -- Category reads plus admin-only category and association mutations.
- `backend/app/api/scanner.py:26-168` -- Admin-only scan job create/list/detail/retry plus queued metadata sync and cover extraction.
- `backend/app/api/files.py:15-181` -- Download, Range-aware stream/HEAD handling, and public cover serving.
- `backend/app/api/recommendations.py:13-127` -- Five authenticated recommendation endpoints.
- `backend/app/api/reading_progress.py:11-66` -- User-scoped reading progress lookup, upsert, and recent-reading endpoints.
- `backend/app/api/notes.py:11-70` -- User-scoped per-book note CRUD endpoints.

## 3. Request Flow

- **1. App bootstrap:** `backend/app/main.py:6-27` creates the app and mounts `api_router` under `settings.API_V1_PREFIX`.
- **2. Router aggregation:** `backend/app/api/router.py:7-14` includes auth, books, scanner, categories, recommendations, files, reading progress, and notes.
- **3. Authentication gate:** Most endpoints depend on `get_current_user` from `backend/app/api/deps.py:11-31`.
- **4. RBAC split:** Mutating book/category routes and all scanner routes depend on `require_admin` at `backend/app/api/deps.py:34-40`, while reader-state routes stay user-scoped through `get_current_user` at `backend/app/api/reading_progress.py:14-66` and `backend/app/api/notes.py:14-70`.
- **5. Search-backed catalog surface:** `GET /books` delegates search, filters, pagination, and sort selection to `BookSearchService` from `backend/app/api/books.py:17-45` and `backend/app/services/search_service.py:20-54`.
- **6. Job-backed scanner surface:** `/scanner/jobs/*` creates and inspects persisted scan jobs, while `/scanner/books/{book_id}/metadata-sync` and `/scanner/books/{book_id}/extract-cover` queue enrich work through `TaskDispatchService` from `backend/app/api/scanner.py:26-168`.
- **7. Range-aware file surface:** `GET /files/stream/{book_id}` and `HEAD /files/stream/{book_id}` expose MIME-aware streaming metadata and single-range partial responses at `backend/app/api/files.py:105-163`.
- **8. Public exception:** `GET /files/cover/{book_id}` intentionally omits authentication in `backend/app/api/files.py:166-181`.

## 4. Pagination and Query Patterns

- **Books list:** Page-based pagination (`page`, `page_size`) with `q`, `author`, `category_id`, `format`, `sort`, and `order` forwarded into `BookSearchService` at `backend/app/api/books.py:17-45`.
- **Categories list:** Offset-style pagination (`skip`, `limit`) at `backend/app/api/categories.py:15-23`.
- **Category books:** Page-based pagination pushed into SQL at `backend/app/api/categories.py:78-108`.
- **Recent reading:** Size-bounded listing via `limit` (`1..100`) at `backend/app/api/reading_progress.py:14-37`.
- **Scan jobs list:** Size-bounded listing via `limit` (`1..100`) at `backend/app/api/scanner.py:72-79`.
- **Recommendations:** All five endpoints accept `count` with bounds `1..50` at `backend/app/api/recommendations.py:16-127`.

## 5. Error-Handling Style

- Guard clauses raise `HTTPException` for missing rows and invalid auth across books, categories, reading progress, notes, files, and auth routes.
- Scanner routes normalize path validation and missing job/book errors into `400` or `404` responses at `backend/app/api/scanner.py:32-66`, `:85-102`, and `:126-149`.
- Reading-progress and note routes map missing owned rows to `404` through service-layer `ValueError` translation at `backend/app/api/reading_progress.py:40-66` and `backend/app/api/notes.py:24-70`.
- Files routes use existence checks, bounded upload-path resolution, and `416` for invalid byte ranges at `backend/app/api/files.py:24-73`, `:105-163`, and `:166-181`.

## 6. Design Notes

- **Flat router layout:** All routers are siblings under a single version prefix.
- **Read vs write split:** Authenticated non-admin users can now read books, categories, files, recommendations, their own reading progress, and their own notes; only mutating book/category routes and scanner-sensitive operations are admin-gated.
- **Public cover endpoint:** Covers remain publicly fetchable to simplify image embedding and unauthenticated catalog-style views.
- **Persisted scanner API:** Batch A replaces the old fire-and-forget scan entrypoints with persisted jobs and item inspection endpoints at `backend/app/api/scanner.py:26-116`.
- **Queued enrich behavior:** Metadata sync and cover extraction are now admin-triggered queue entrypoints, keeping router work limited to validation plus Celery dispatch at `backend/app/api/scanner.py:119-168`.
- **Range-aware file streaming:** The files router now exposes inline streaming metadata and partial-content support without adding a separate download-only protocol at `backend/app/api/files.py:105-163`.
- **User-owned reader state:** Batch C keeps reader-state routes fully scoped by `current_user.id` instead of introducing any admin override path at `backend/app/services/reading_service.py:15-73` and `backend/app/services/note_service.py:14-58`.
