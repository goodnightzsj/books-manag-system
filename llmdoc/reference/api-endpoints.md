# API Endpoints Reference

## 1. Core Summary

The API exposes 39 routed endpoints across eight routers under `/api/v1`. Public endpoints are limited to `POST /auth/register`, `POST /auth/login`, `GET /health`, `GET /`, and `GET /files/cover/{book_id}`. Most read endpoints require any authenticated user; mutating book/category routes and all scanner routes require admin role, while reading-progress and note routes are scoped to the current authenticated user.

## 2. Source of Truth

- Router aggregation: `backend/app/api/router.py:1-14`
- Auth dependencies: `backend/app/api/deps.py:11-40`
- Mounted prefix: `backend/app/main.py:26-27`

## 3. Auth Router (`/api/v1/auth`)

Source: `backend/app/api/auth.py:10-61`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| POST | `/auth/register` | No | `register` | Creates a normal user. |
| POST | `/auth/login` | No | `login` | Returns JWT bearer token. |
| GET | `/auth/me` | User | `get_current_user_info` | Returns current user profile. |

## 4. Books Router (`/api/v1/books`)

Source: `backend/app/api/books.py:17-118`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/books` | User | `get_books` | Page-based pagination with `q`, `author`, `category_id`, `format`, `sort`, and `order` forwarded to `BookSearchService`. |
| GET | `/books/{book_id}` | User | `get_book` | Returns one book or 404. |
| POST | `/books` | Admin | `create_book` | Accepts `FileFormat` enum input, refreshes `books.search_vector` after insert, and maps unique `file_path` / `isbn` conflicts to `409 Conflict` at `backend/app/api/books.py:18-90`. |
| PUT | `/books/{book_id}` | Admin | `update_book` | Partial update via `model_dump(exclude_unset=True)`, refreshes `books.search_vector`, and maps unique `file_path` / `isbn` conflicts to `409 Conflict` at `backend/app/api/books.py:18-118`. |
| DELETE | `/books/{book_id}` | Admin | `delete_book` | Hard delete, 204. |

## 5. Categories Router (`/api/v1/categories`)

Source: `backend/app/api/categories.py:12-164`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/categories` | User | `get_categories` | Uses `skip`/`limit`. |
| GET | `/categories/{category_id}` | User | `get_category` | Returns one category or 404. |
| POST | `/categories` | Admin | `create_category` | Rejects duplicate names. |
| DELETE | `/categories/{category_id}` | Admin | `delete_category` | Hard delete, 204. |
| GET | `/categories/{category_id}/books` | User | `get_category_books` | SQL-level pagination with `page` and `page_size`. |
| POST | `/categories/{category_id}/books/{book_id}` | Admin | `add_book_to_category` | Idempotent association add. |
| DELETE | `/categories/{category_id}/books/{book_id}` | Admin | `remove_book_from_category` | Removes association if present. |

## 6. Scanner Router (`/api/v1/scanner`)

Source: `backend/app/api/scanner.py:26-168`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| POST | `/scanner/jobs/directory` | Admin | `create_directory_scan_job` | Restricts the path under `BOOKS_DIR`, creates a persisted job, and queues the root scan task. |
| POST | `/scanner/jobs/file` | Admin | `create_file_scan_job` | Restricts the file under `BOOKS_DIR`, requires a supported format, creates a persisted single-file job, and queues it. |
| GET | `/scanner/jobs` | Admin | `list_scan_jobs` | Returns recent persisted jobs with aggregate counters. |
| GET | `/scanner/jobs/{job_id}` | Admin | `get_scan_job` | Returns one scan job or 404. |
| GET | `/scanner/jobs/{job_id}/items` | Admin | `get_scan_job_items` | Returns persisted item rows for the selected job. |
| POST | `/scanner/jobs/{job_id}/retry-failed` | Admin | `retry_failed_scan_items` | Queues retries for failed items in one job. |
| POST | `/scanner/books/{book_id}/metadata-sync` | Admin | `queue_metadata_sync` | Queues metadata enrichment on the enrich queue; worker lookup order is Douban ISBN -> Douban title -> Google Books ISBN. |
| POST | `/scanner/books/{book_id}/extract-cover` | Admin | `queue_cover_extract` | Queues local extraction or remote download; the remote source comes only from persisted `book_metadata.cover_url`. |

## 7. Reading Progress Router (`/api/v1/reading-progress`)

Source: `backend/app/api/reading_progress.py:11-66`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/reading-progress/recent` | User | `get_recent_reading` | Returns current-user recent reading rows with joined book summary data. |
| GET | `/reading-progress/{book_id}` | User | `get_reading_progress` | Returns only the current user's progress row for one book, or 404. |
| PUT | `/reading-progress/{book_id}` | User | `upsert_reading_progress` | Creates or updates the current user's progress row and accepts locator payloads for PDF/EPUB/TXT. |

## 8. Notes Router (`/api/v1/books/{book_id}/notes`)

Source: `backend/app/api/notes.py:11-70`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/books/{book_id}/notes` | User | `list_notes` | Lists only the current user's notes for one book. |
| POST | `/books/{book_id}/notes` | User | `create_note` | Creates one note scoped to the current user and book. |
| PUT | `/books/{book_id}/notes/{note_id}` | User | `update_note` | Updates only a note owned by the current user. |
| DELETE | `/books/{book_id}/notes/{note_id}` | User | `delete_note` | Deletes only a note owned by the current user. |

## 8b. Annotations Router (`/api/v1/books/{book_id}`)

Source: `backend/app/api/annotations.py`

Independent `bookmarks` and `annotations` tables were introduced in migration `004`. The legacy `ReadingProgress.bookmarks/notes` JSON fields are no longer written.

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/books/{book_id}/bookmarks` | User | `list_bookmarks` | Current user's bookmarks for this book. |
| POST | `/books/{book_id}/bookmarks` | User | `create_bookmark` | Takes a locator, optional title and note. |
| PUT | `/books/{book_id}/bookmarks/{bookmark_id}` | User | `update_bookmark` | Owner-scoped partial update. |
| DELETE | `/books/{book_id}/bookmarks/{bookmark_id}` | User | `delete_bookmark` | Owner-scoped. |
| GET | `/books/{book_id}/annotations` | User | `list_annotations` | Current user's highlights and margin notes. |
| POST | `/books/{book_id}/annotations` | User | `create_annotation` | `locator_start` required, optional range end / highlight text / color. |
| PUT | `/books/{book_id}/annotations/{annotation_id}` | User | `update_annotation` | Owner-scoped partial update. |
| DELETE | `/books/{book_id}/annotations/{annotation_id}` | User | `delete_annotation` | Owner-scoped. |

## 9. Files Router (`/api/v1/files`)

Source: `backend/app/api/files.py:15-181`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/files/download/{book_id}` | User | `download_book` | Returns attachment `FileResponse`. |
| GET | `/files/stream/{book_id}` | User | `stream_book` | Streams inline with format-specific MIME type and supports single `Range` requests with `206 Partial Content`. |
| HEAD | `/files/stream/{book_id}` | User | `head_stream_book` | Returns `Accept-Ranges`, `Content-Length`, and `Content-Type` without streaming the body. |
| GET | `/files/cover/{book_id}` | No | `get_book_cover` | Public file response; resolves the upload path under `UPLOADS_DIR` before serving. |

## 10. Recommendations Router (`/api/v1/recommendations`)

Source: `backend/app/api/recommendations.py:13-127`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/recommendations/random` | User | `get_random_recommendations` | Samples from top-rated books or falls back to `random()`. |
| GET | `/recommendations/category/{category_id}` | User | `get_category_recommendations` | Query-based top-rated books in one category. |
| GET | `/recommendations/trending` | User | `get_trending_books` | Ordered by `rating DESC, rating_count DESC`. |
| GET | `/recommendations/personalized` | User | `get_personalized_recommendations` | Uses completed reads; falls back to trending. |
| GET | `/recommendations/similar/{book_id}` | User | `get_similar_books` | Same author and/or overlapping categories. |

## 11. App-Level Endpoints

Source: `backend/app/main.py:29-39`

| Method | Path | Auth | Handler | Notes |
|---|---|---|---|---|
| GET | `/` | No | `root` | Basic service info and docs pointer. |
| GET | `/health` | No | `health_check` | Returns `{"status": "healthy"}`. |
