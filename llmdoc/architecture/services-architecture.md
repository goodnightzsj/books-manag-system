# Architecture of the Services Layer

## 1. Identity

- **What it is:** The service layer for scanning files, extracting metadata, performing online enrichment, and managing covers.
- **Purpose:** Translate ebook files on disk into normalized `Book` records and associated cover assets.

## 2. Core Components

- `backend/app/services/file_access_service.py:26-107` -- `FileAccessService` for path restriction, supported-file discovery, snapshots, and MIME lookup.
- `backend/app/services/scan_job_service.py:11-140` -- `ScanJobService` for `scan_jobs` / `scan_job_items` lifecycle and counters.
- `backend/app/services/task_dispatch_service.py:7-65` -- `TaskDispatchService` as the Celery dispatch boundary for scan, hash, enrich, and maintenance work.
- `backend/app/services/scanner_service.py:8-36` -- `ScanService`, now limited to single-item orchestration and hash-followup decisions.
- `backend/app/services/book_ingest_service.py:17-266` -- `BookIngestService` for scanned-book upsert, hash application, and duplicate-book merge; duplicate field merge is centralized in `MERGEABLE_BOOK_FIELDS` at `backend/app/services/book_ingest_service.py:25-42`.
- `backend/app/services/hash_service.py:9-66` -- `HashService` for hash decisions, SHA-256 computation, and error classification.
- `backend/app/services/search_service.py:13-112` -- `BookSearchService` for FTS/trigram lookup, category/format filtering, sort selection, and `search_vector` refresh.
- `backend/app/services/reading_service.py:11-71` -- `ReadingProgressService` for per-user progress lookup, upsert, auto status transitions, and recent-reading queries; progress upsert no longer writes legacy `notes` / `bookmarks` fields at `backend/app/services/reading_service.py:22-42`.
- `backend/app/services/note_service.py:10-58` -- `NoteService` for per-user `book_notes` list/create/update/delete.
- `backend/app/services/metadata_service.py:17-106` -- `MetadataExtractor` for local file metadata.
- `backend/app/services/metadata_service.py:109-226` -- `OnlineMetadataService` for Douban and Google Books lookups.
- `backend/app/services/metadata_service.py:238-334` -- `MetadataSyncService` for provider fallback, non-destructive field merge, metadata bookkeeping, and search refresh.
- `backend/app/services/cover_service.py:15-148` -- `CoverService` for `ensure_cover()`, local extraction, remote download, and thumbnails.
- `backend/app/tasks/scan_tasks.py:14-110` -- Celery scan root/item/retry tasks with hash dispatch after successful ingest.
- `backend/app/tasks/hash_tasks.py:11-43` -- Celery hash task for SHA-256 computation, duplicate detection, and `scan_job_items.detected_hash` backfill.
- `backend/app/tasks/metadata_tasks.py:13-48` -- Celery metadata sync task with optional cover follow-up.
- `backend/app/tasks/cover_tasks.py:10-43` -- Celery cover task for local extraction or remote download.
- `backend/app/tasks/maintenance_tasks.py:10-81` -- Celery maintenance task for stalled job/item reconciliation.
- `backend/app/api/scanner.py:23-163` -- API orchestration layer around scan jobs and async metadata/cover queue endpoints.
- `backend/app/api/files.py:15-174` -- Download, Range-aware streaming, HEAD metadata, and public cover serving.
- `backend/app/core/config.py:6-46` -- Runtime settings consumed by queues, maintenance cutoffs, and enrich workers.

## 3. Execution Flow

### Phase 1 -- Scan Jobs

- **1. API entry:** `POST /scanner/jobs/directory` and `POST /scanner/jobs/file` validate the requested path through `FileAccessService` and create persisted job rows at `backend/app/api/scanner.py:29-68`.
- **2. Job persistence:** `ScanJobService.create_job()` writes `scan_jobs` rows with normalized paths and creator IDs at `backend/app/services/scan_job_service.py:15-26`.
- **3. Celery dispatch:** `TaskDispatchService` enqueues root tasks onto `settings.BOOKS_SCAN_QUEUE` at `backend/app/services/task_dispatch_service.py:7-22`.
- **4. Root task claim:** `run_directory_job()` and `run_file_job()` claim queued jobs, discover supported files, and seed `scan_job_items` at `backend/app/tasks/scan_tasks.py:12-55`.
- **5. Item processing:** `process_scan_item()` claims a queued item, runs `ScanService.process_file()`, writes item status, finalizes the job when possible, and conditionally dispatches hash computation at `backend/app/tasks/scan_tasks.py:61-110`.
- **6. Single-item orchestration:** `ScanService.process_file()` snapshots the file, extracts local metadata, and delegates to `BookIngestService.upsert_scanned_book()` at `backend/app/services/scanner_service.py:21-36`.
- **7. Hash computation:** `hash.compute_book_hash()` resolves the current file path, computes SHA-256, and calls `BookIngestService.apply_hash_result()` at `backend/app/tasks/hash_tasks.py:11-43`.
- **8. Duplicate merge:** `BookIngestService.apply_hash_result()` selects a canonical `Book` and `merge_duplicate_books()` rebinds reading progress, notes, category links, and scan job item references before deleting the duplicate row at `backend/app/services/book_ingest_service.py:115-192`; non-file duplicate field merge now iterates the centralized `MERGEABLE_BOOK_FIELDS` list at `backend/app/services/book_ingest_service.py:25-42` and `:208-224`.

### Phase 2 -- Online Enrichment

- **9. API entry:** `POST /scanner/books/{book_id}/metadata-sync` validates the target book and queues enrich work at `backend/app/api/scanner.py:119-136`.
- **10. Celery dispatch:** `TaskDispatchService.enqueue_metadata_sync()` sends the task to `settings.BOOKS_ENRICH_QUEUE` at `backend/app/services/task_dispatch_service.py:31-38`.
- **11. External lookup order:** `OnlineMetadataService.fetch_best_match()` tries Douban ISBN -> Douban title -> Google Books ISBN at `backend/app/services/metadata_service.py:113-135`.
- **12. Metadata merge:** `MetadataSyncService.sync_book()` only applies non-empty fields unless `force=True`, updates `source_provider` / `metadata_synced_at`, persists merged `book_metadata`, and refreshes `books.search_vector` at `backend/app/services/metadata_service.py:263-305`.
- **13. Cover follow-up:** `metadata.sync_book_metadata()` optionally queues `cover.extract_or_download_cover` after a successful lookup at `backend/app/tasks/metadata_tasks.py:27-36`.

### Phase 3 -- Cover Sync

- **14. API entry:** `POST /scanner/books/{book_id}/extract-cover` validates the target book and queues cover work at `backend/app/api/scanner.py:139-163`.
- **15. Celery dispatch:** `TaskDispatchService.enqueue_cover_sync()` sends the task to `settings.BOOKS_ENRICH_QUEUE` at `backend/app/services/task_dispatch_service.py:40-58`.
- **16. Strategy selection:** `CoverService.ensure_cover()` chooses local-first or remote-first behavior and falls back between them at `backend/app/services/cover_service.py:24-46`.
- **17. Local extraction:** `extract_cover_from_pdf()` and `extract_cover_from_epub()` still cover PDF and EPUB at `backend/app/services/cover_service.py:61-91`.
- **18. Remote download and thumbnails:** `download_cover()` accepts only `http` / `https` URLs and `_generate_thumbnail()` writes bounded thumbnails at `backend/app/services/cover_service.py:93-148`.

### Phase 4 -- Maintenance Reconciliation

- **19. Beat schedule:** `celery_app.conf.beat_schedule` queues `maintenance.reconcile_stalled_jobs` on `settings.BOOKS_MAINTENANCE_QUEUE` at `backend/app/celery_app.py:27-33`.
- **20. Stalled item repair:** `reconcile_stalled_jobs()` marks long-running `processing` items as failed at `backend/app/tasks/maintenance_tasks.py:19-36`.
- **21. Job reconciliation:** The same task marks stale empty jobs failed and closes already-processed jobs through `ScanJobService.maybe_finalize_job()` at `backend/app/tasks/maintenance_tasks.py:38-69` and `backend/app/services/scan_job_service.py:98-117`.

## 4. Format Support Matrix

| Extension | Local metadata | Local cover extraction | Notes |
|---|---|---|---|
| `.pdf` | PyPDF2 | Yes | Title/author/subject/page count |
| `.epub` | ebookmeta | Yes | Richest local metadata support |
| `.mobi` | Basic fallback | No | `_extract_mobi()` currently falls back to filename parsing |
| `.azw3` | Basic fallback | No | No dedicated parser |
| `.txt` | Basic + first lines | No | First non-empty lines become short description |
| `.djvu` | Basic fallback | No | No dedicated parser |

## 5. External Integration Notes

- `OnlineMetadataService` is synchronous and created with `douban_api_url=settings.DOUBAN_API_URL` from the scanner API at `backend/app/api/scanner.py:127`.
- Douban requests use `GET /v2/book/isbn/{isbn}` or `GET /v2/book/search?q=...` through `httpx.Client` at `backend/app/services/metadata_service.py:114-125`.
- Google Books queries `https://www.googleapis.com/books/v1/volumes` at `backend/app/services/metadata_service.py:151-175`.

## 6. Current Limits

- Celery now wires scan, hash, metadata, cover, and maintenance tasks through `backend/app/celery_app.py:13-34`, and beat schedules stalled-job reconciliation using `settings.MAINTENANCE_RECONCILE_INTERVAL_SECONDS` from `backend/app/core/config.py:20-22`.
- Metadata and cover enrichment remain admin-triggered queue operations from `backend/app/api/scanner.py:119-163`; scan ingest still does not auto-run metadata sync.
- Initial ingest still uses file snapshot checks to decide whether rehash is needed, but duplicate identity now converges on `content_hash` once `hash.compute_book_hash()` finishes at `backend/app/services/hash_service.py:20-45` and `backend/app/services/book_ingest_service.py:97-174`.
- MOBI, AZW3, and DJVU still have shallow metadata extraction.
- Cover extraction is only implemented for PDF and EPUB.
