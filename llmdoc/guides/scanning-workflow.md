# How the Book Scanning Pipeline Works

This guide describes the current admin-only scan-job and enrichment flow implemented across `backend/app/api/scanner.py`, `backend/app/tasks/scan_tasks.py`, and the scanner services.

## Phase 1 -- Create Scan Jobs

1. **Trigger a directory scan:** Call `POST /scanner/jobs/directory` with `{"directory": "/path/inside/books"}` at `backend/app/api/scanner.py:29-49`.
2. **Path restriction:** `FileAccessService.resolve_scan_root()` normalizes the path, keeps it under `settings.BOOKS_DIR`, and rejects missing targets at `backend/app/services/file_access_service.py:36-43`.
3. **Persist the job:** `ScanJobService.create_job()` writes a `scan_jobs` row with `job_type`, requested path, normalized path, and creator at `backend/app/services/scan_job_service.py:15-26`.
4. **Queue the root task:** `TaskDispatchService.enqueue_scan_directory()` sends the job to `settings.BOOKS_SCAN_QUEUE` at `backend/app/services/task_dispatch_service.py:8-10`.
5. **Immediate response:** The API returns `job_id`, `status="queued"`, and a message instead of starting an untracked background task at `backend/app/api/scanner.py:40-49`.

## Phase 1b -- Create a Single-File Job

6. **Trigger a file scan:** Call `POST /scanner/jobs/file` with `{"file_path": "/path/inside/books/book.pdf"}` at `backend/app/api/scanner.py:52-69`.
7. **Supported-format check:** `FileAccessService.ensure_supported_file()` validates both the path boundary and the extension at `backend/app/services/file_access_service.py:54-59`.
8. **Persist and queue:** The API writes a `scan_jobs` row with `job_type="scan_file"` and dispatches `run_file_job()` through `TaskDispatchService.enqueue_scan_file()` at `backend/app/api/scanner.py:58-67` and `backend/app/services/task_dispatch_service.py:12-14`.

## Phase 2 -- Worker Execution

9. **Claim the queued job:** `run_directory_job()` or `run_file_job()` claims the job, flips it to `running`, and stamps `started_at` through `ScanJobService.claim_job()` at `backend/app/tasks/scan_tasks.py:12-27`, `:35-49`, and `backend/app/services/scan_job_service.py:39-47`.
10. **Discover supported files:** `FileAccessService.iter_supported_files()` yields normalized files for `.pdf`, `.epub`, `.mobi`, `.azw3`, `.txt`, and `.djvu` at `backend/app/services/file_access_service.py:27-34` and `:61-75`.
11. **Persist job items:** `ScanJobService.add_items()` creates `scan_job_items` rows and updates `job.total_items` at `backend/app/services/scan_job_service.py:49-65`.
12. **Queue per-file work:** Each discovered item is sent to `process_scan_item()` from the root task at `backend/app/tasks/scan_tasks.py:21-26` and `:43-48`.
13. **Claim one item:** `ScanJobService.claim_item()` moves an item from `queued` or `failed` to `processing` at `backend/app/services/scan_job_service.py:67-75`.
14. **Process one file:** `ScanService.process_file()` snapshots the file, extracts local metadata, calls `BookIngestService.upsert_scanned_book()`, and commits once per item at `backend/app/services/scanner_service.py:21-36`.
15. **Decide whether hash should follow:** `HashService.should_hash()` and `BookIngestService.upsert_scanned_book()` still use the current file snapshot (`file_path`, `file_size`, `file_mtime`) to decide whether a later hash run is required at `backend/app/services/hash_service.py:20-45` and `backend/app/services/book_ingest_service.py:30-95`.
16. **Finalize scan-item status first:** `ScanJobService.mark_item_finished()` updates the item row and aggregate counters before any hash follow-up, and `maybe_finalize_job()` closes the scan job when all items are processed at `backend/app/services/scan_job_service.py:77-117`.
17. **Dispatch async hash work:** If the ingest result requests hashing, `process_scan_item()` enqueues `hash.compute_book_hash` through `TaskDispatchService.enqueue_compute_hash()`; dispatch failures are recorded on `books.hash_status` / `books.hash_error` without reopening the scan item at `backend/app/tasks/scan_tasks.py:76-84` and `backend/app/services/task_dispatch_service.py:24-29`.
18. **Resolve content identity:** `compute_book_hash()` resolves the current book file, computes SHA-256, and calls `BookIngestService.apply_hash_result()` at `backend/app/tasks/hash_tasks.py:11-31`.
19. **Merge duplicates by hash:** When another row already has the same `content_hash`, `apply_hash_result()` chooses a canonical `Book` by earliest `created_at`, then rebinds reading progress, notes, category links, and scan job item references before deleting the duplicate row at `backend/app/services/book_ingest_service.py:107-174`.
20. **Zero-item jobs:** If a valid path yields no supported files, `maybe_finalize_job()` closes the job as `completed` with `total_items=0` at `backend/app/services/scan_job_service.py:98-106`.

## Phase 3 -- Inspect and Retry Jobs

21. **List jobs:** Call `GET /scanner/jobs` to retrieve recent persisted jobs and aggregate counters at `backend/app/api/scanner.py:72-79`.
22. **Inspect one job:** Call `GET /scanner/jobs/{job_id}` to retrieve one persisted job row at `backend/app/api/scanner.py:82-91`.
23. **Inspect items:** Call `GET /scanner/jobs/{job_id}/items` to retrieve file-level item rows for a job at `backend/app/api/scanner.py:94-105`.
24. **Retry failed items:** Call `POST /scanner/jobs/{job_id}/retry-failed`; the router queues `retry_failed_items()`, which resets failed items to `queued` and dispatches them again at `backend/app/api/scanner.py:108-119`, `backend/app/tasks/scan_tasks.py:83-96`, and `backend/app/services/scan_job_service.py:128-140`.

## Phase 4 -- Metadata Enrichment

25. **Trigger metadata sync:** Call `POST /scanner/books/{book_id}/metadata-sync`; the router validates the book and queues enrich work at `backend/app/api/scanner.py:119-136`.
26. **Queue enrich work:** `TaskDispatchService.enqueue_metadata_sync()` dispatches the task onto `settings.BOOKS_ENRICH_QUEUE` at `backend/app/services/task_dispatch_service.py:31-38`.
27. **Lookup priority:** `OnlineMetadataService.fetch_best_match()` tries providers in this order: Douban by ISBN -> Douban by title -> Google Books by ISBN at `backend/app/services/metadata_service.py:113-135`.
28. **Non-destructive merge:** `MetadataSyncService.sync_book()` only applies non-empty fields unless `force=true`, updates `source_provider` / `metadata_synced_at`, persists merged metadata, and refreshes `books.search_vector` at `backend/app/services/metadata_service.py:263-305`.
29. **Optional cover follow-up:** `metadata.sync_book_metadata()` queues `cover.extract_or_download_cover` after successful lookup, using metadata `cover_url` when available, at `backend/app/tasks/metadata_tasks.py:13-48`.

## Phase 5 -- Cover Sync

30. **Trigger cover sync:** Call `POST /scanner/books/{book_id}/extract-cover` at `backend/app/api/scanner.py:139-163`.
31. **Strategy selection:** `CoverService.ensure_cover()` chooses local-first or remote-first behavior and falls back between them at `backend/app/services/cover_service.py:24-46`.
32. **Supported local extraction formats:** PDF first-page render and EPUB embedded cover remain the only local extractors at `backend/app/services/cover_service.py:61-91`.
33. **Remote download and thumbnails:** `download_cover()` accepts only `http` / `https` URLs and `_generate_thumbnail()` writes bounded thumbnails at `backend/app/services/cover_service.py:93-148`.

## Phase 6 -- Maintenance Reconciliation

34. **Beat schedule:** Celery beat queues `maintenance.reconcile_stalled_jobs` on the maintenance queue at `backend/app/celery_app.py:27-33`.
35. **Stalled item repair:** `reconcile_stalled_jobs()` marks long-running `processing` items failed at `backend/app/tasks/maintenance_tasks.py:19-36`.
36. **Job reconciliation:** The same task marks stale empty jobs failed and closes already-processed jobs through `ScanJobService.maybe_finalize_job()` at `backend/app/tasks/maintenance_tasks.py:38-69` and `backend/app/services/scan_job_service.py:98-117`.

## Error Scenarios and Current Limits

- **Admin role required:** All scanner endpoints use `require_admin`; non-admin callers receive `403` from `backend/app/api/deps.py:34-40`.
- **Outside-path scans are rejected:** Any scan target outside `settings.BOOKS_DIR` fails with `400` from `FileAccessService` at `backend/app/services/file_access_service.py:36-59`.
- **Unsupported single-file scans are rejected:** `ensure_supported_file()` returns `400` for extensions outside the supported set at `backend/app/services/file_access_service.py:54-59`.
- **Jobs are now persisted and queryable:** Directory and file scans return a `job_id`, and progress lives in `scan_jobs` / `scan_job_items` instead of `BackgroundTasks` memory.
- **Identity switches asynchronously:** Initial ingest still starts from file snapshot checks, so duplicate rows can exist briefly until `hash.compute_book_hash()` finishes; after that, identity converges on `content_hash` through `backend/app/services/book_ingest_service.py:97-174`.
- **Job completion does not wait for hash completion:** `scan_jobs` track scan-item ingest status, while later hash results land on `books.hash_status`, `books.hash_error`, and optional `scan_job_items.detected_hash` at `backend/app/tasks/scan_tasks.py:74-84` and `backend/app/tasks/hash_tasks.py:21-38`.
- **Enrichment and maintenance tasks are wired into Celery:** `backend/app/celery_app.py:13-34` now imports scan/hash/metadata/cover/maintenance tasks and schedules stalled-job reconciliation through beat.
- **Metadata and cover remain admin-triggered:** `POST /scanner/books/{book_id}/metadata-sync` and `POST /scanner/books/{book_id}/extract-cover` queue work on demand at `backend/app/api/scanner.py:119-163`; scan ingest still does not auto-run metadata sync.
- **MOBI / AZW3 / DJVU metadata is shallow:** These formats still fall back to basic filename parsing in `backend/app/services/metadata_service.py:18-22` and `:79-101`.
- **Douban proxy dependency remains:** Douban lookups still rely on `settings.DOUBAN_API_URL`, defaulting to `https://douban.uieee.com`.
