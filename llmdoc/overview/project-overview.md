# Books Management System

## 1. Identity

- **What it is:** A Chinese-focused ebook library management backend with local file scanning, metadata enrichment, cover handling, and rule-based recommendations.
- **Purpose:** Organize and expose a personal ebook collection through a REST API backed by PostgreSQL.

## 2. High-Level Description

This is a backend-only Python service. The API is mounted under `settings.API_V1_PREFIX` at `backend/app/main.py:26-27` and currently covers authentication, book CRUD, category management, scanner operations, file serving, recommendations, reading-progress sync, and per-book notes. The stack is synchronous for request handling and DB access, with Celery now running scan, hash, metadata, cover, and maintenance tasks through `backend/app/celery_app.py:7-34`, `backend/app/tasks/scan_tasks.py:12-96`, `backend/app/tasks/metadata_tasks.py:13-48`, `backend/app/tasks/cover_tasks.py:10-43`, and `backend/app/tasks/maintenance_tasks.py:10-81`. FastAPI handlers still use synchronous SQLAlchemy sessions from `backend/app/db/base.py:5-17`, and the metadata/cover services still use synchronous HTTP clients at `backend/app/services/metadata_service.py:113-200` and `backend/app/services/cover_service.py:24-111`.

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web Framework | FastAPI 0.109 |
| ORM | SQLAlchemy 2.0 sync engine |
| Database | PostgreSQL |
| Cache / Broker | Redis |
| Migrations | Alembic |
| Auth | JWT + bcrypt |
| File / Metadata libs | ebookmeta, PyPDF2, PyMuPDF, Pillow, httpx |
| Containerization | Docker |

## 4. Key Capabilities

- **Job-based file scanning:** Admin scans now create persisted `scan_jobs` and `scan_job_items` rows through `backend/app/api/scanner.py:29-119`, `backend/app/models/scan_job.py:37-74`, and `backend/app/tasks/scan_tasks.py:12-96`.
- **Path-restricted scanner API:** Scanner paths are normalized and restricted under `settings.BOOKS_DIR` by `FileAccessService` at `backend/app/services/file_access_service.py:36-59`.
- **Single-item scan orchestration:** `ScanService.process_file()` handles snapshot -> metadata extraction -> `Book` upsert and returns whether hash computation should follow at `backend/app/services/scanner_service.py:8-36`.
- **Local metadata extraction:** PDF, EPUB, TXT, and filename-based extraction live in `backend/app/services/metadata_service.py:10-101`.
- **Content-hash identity:** `HashService`, `hash.compute_book_hash`, and `BookIngestService.apply_hash_result()` now compute SHA-256 asynchronously, backfill `scan_job_items.detected_hash`, and merge duplicate books by `content_hash` at `backend/app/services/hash_service.py:9-66`, `backend/app/tasks/hash_tasks.py:11-43`, and `backend/app/services/book_ingest_service.py:97-174`.
- **Search-backed catalog listing:** `BookSearchService` powers `GET /books` with FTS + trigram matching, category/format filters, and sort selection at `backend/app/services/search_service.py:13-112` and `backend/app/api/books.py:17-45`.
- **Reading progress sync:** `ReadingProgressService` and `reading_progress` routes provide per-user locator-based progress lookup, upsert, and recent-reading listing at `backend/app/services/reading_service.py:11-73` and `backend/app/api/reading_progress.py:11-66`.
- **Book notes:** `NoteService` and `notes` routes provide user-scoped CRUD over `book_notes` at `backend/app/services/note_service.py:10-58` and `backend/app/api/notes.py:11-70`.
- **Online enrichment:** `MetadataSyncService` queues provider fallback lookup, non-destructive field merge, and `search_vector` refresh through `backend/app/services/metadata_service.py:229-334` and `backend/app/tasks/metadata_tasks.py:13-48`.
- **Cover handling:** `CoverService.ensure_cover()` supports local-first or remote-first extraction/download strategy and is queued through `backend/app/services/cover_service.py:15-148` and `backend/app/tasks/cover_tasks.py:10-43`.
- **JWT auth + RBAC:** `get_current_user` and `require_admin` are defined in `backend/app/api/deps.py:11-40`.
- **Recommendations:** Five rule-based recommendation endpoints live in `backend/app/api/recommendations.py:16-127`.
- **File serving:** Download, Range-aware stream/HEAD responses, and public cover access live in `backend/app/api/files.py:24-181`.

## 5. Key Paths

- `backend/app/main.py:6-39` -- FastAPI app creation, CORS, router mount, root and health endpoints.
- `backend/app/api/router.py:1-14` -- Aggregates the eight API routers.
- `backend/app/api/` -- Route handlers for auth, books, categories, scanner, files, recommendations, reading progress, and notes.
- `backend/app/core/config.py:6-46` -- Central runtime settings, including enrich and maintenance queue timing.
- `backend/app/db/base.py:5-17` -- SQLAlchemy engine, session factory, and request-scoped session dependency.
- `backend/app/models/` -- ORM models for users, books/categories, reading progress, scan jobs, and notes.
- `backend/app/services/` -- Scanner, search, reader-state, metadata, and cover business logic.
- `backend/alembic/versions/001_initial.py:19-126` -- Current schema baseline.
- `backend/entrypoint.sh:4-95` -- Container role selection, readiness checks, migrations, admin bootstrap, and API/worker/beat startup.

## 6. Current State and Constraints

- **Schema baseline changed after Batch A:** The original baseline remains `backend/alembic/versions/001_initial.py:19-106`, but Batch A adds `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:1-143` for scan jobs, note storage, reading locator support, and book hash/search metadata.
- **Write access is role-gated:** Mutating book/category routes and all scanner routes use `require_admin` from `backend/app/api/deps.py:34-40`.
- **Deployment defaults are hardened:** `DEBUG` now defaults to `False` in `backend/app/core/config.py:7-8`, admin bootstrap is env-driven in `backend/entrypoint.sh:45-76`, and uvicorn starts without `--reload` at `backend/entrypoint.sh:87`.
- **Still Docker-oriented:** The entrypoint still assumes service names `postgres` and `redis` at `backend/entrypoint.sh:6-31`; there is still no `docker-compose.yml` in the repo.
- **Scanner is now persisted and queryable:** Job creation and progress lookup live in `backend/app/api/scanner.py:26-116`, with task state stored in `backend/app/models/scan_job.py:37-74`.
- **Metadata and cover are now async admin operations:** `POST /scanner/books/{book_id}/metadata-sync` and `POST /scanner/books/{book_id}/extract-cover` queue work instead of doing synchronous enrichment in the router at `backend/app/api/scanner.py:119-168`.
- **Maintenance reconciliation is scheduled:** Celery beat queues stalled-job repair through `backend/app/celery_app.py:27-33` using timeouts from `backend/app/core/config.py:20-22`.
- **Schema layer now covers reader state too:** `backend/app/schemas/scanner.py:1-60`, `backend/app/schemas/reading.py:10-75`, and `backend/app/schemas/note.py:9-34` now cover scanner jobs, locator-based reading progress, and book notes; scanner maintenance/admin responses still include some ad-hoc dict payloads, as tracked in `llmdoc/reference/schemas-reference.md`.
- **Search persistence is broader but still partial:** admin create/update and metadata sync refresh `books.search_vector` through `backend/app/api/books.py:63-99` and `backend/app/services/metadata_service.py:298-305`, but scan ingest still does not auto-run metadata sync.
- **Legacy test script is environment-driven now:** `backend/test_api.py:10-12` reads `ADMIN_USERNAME` and `ADMIN_PASSWORD` from the environment, matching the bootstrap model.
- **Hash merge rule is now active:** duplicate content is resolved to a canonical `Book` chosen by earliest `created_at`, then associated reading progress, notes, category links, and scan job item references are rebound inside `backend/app/services/book_ingest_service.py:121-174`.
- **Async features need multiple runtime roles:** `backend/entrypoint.sh:4-95` now splits API, worker, and beat startup with `APP_ROLE=api|worker|beat`.
