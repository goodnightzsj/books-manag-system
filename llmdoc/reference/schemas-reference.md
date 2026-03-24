# Pydantic Schemas Reference

## 1. Core Summary

Pydantic schemas are currently defined for Book, User, Category, scanner job payloads/responses, locator-based reading progress, and book notes. The exported schema surface is collected in `backend/app/schemas/__init__.py:1-24`.

## 2. Source of Truth

- `backend/app/schemas/book.py:9-46`
- `backend/app/schemas/user.py:7-32`
- `backend/app/schemas/category.py:6-19`
- `backend/app/schemas/scanner.py:8-70`
- `backend/app/schemas/reading.py:10-75`
- `backend/app/schemas/note.py:9-34`
- `backend/app/schemas/__init__.py:1-24`

## 3. Schema Inventory

### Book Schemas

Source: `backend/app/schemas/book.py:6-46`

- `BookBase` -- shared descriptive fields.
- `BookCreate` -- extends `BookBase` with `file_path` and `file_format`.
- `BookUpdate` -- partial update model for a subset of book fields.
- `Book` -- response model with `id`, `cover_url`, `file_format`, `file_size`, `page_count`, `rating`, `rating_count`, `tags`, `created_at`, `updated_at`.
- `BookList` -- pagination wrapper.

### User Schemas

Source: `backend/app/schemas/user.py:7-32`

- `UserBase` -- `username`, `email`, `display_name`.
- `UserCreate` -- adds password with `min_length=6`.
- `UserLogin` -- login payload.
- `User` -- response model with `id`, `role`, and `created_at`.
- `Token` -- access token response.
- `TokenData` -- decoded token payload helper.

Note: `role` is typed as `UserRole` in the response schema at `backend/app/schemas/user.py:19-22`, matching the ORM enum.

### Category Schemas

Source: `backend/app/schemas/category.py:6-19`

- `CategoryBase` -- `name`, `description`, `parent_id`.
- `CategoryCreate` -- same fields as `CategoryBase`.
- `Category` -- response model with `id` and `created_at`.

### Scanner Schemas

Source: `backend/app/schemas/scanner.py:8-70`

- `ScanJobType` -- literal domain for `scan_directory`, `scan_file`, `rehash`, and `resync_metadata`.
- `ScanJobStatus` -- literal domain for persisted job state.
- `ScanItemStatus` -- literal domain for persisted item state.
- `ScanDirectoryRequest` -- request body for directory-job creation.
- `ScanFileRequest` -- request body for single-file job creation.
- `ScanJobCreatedResponse` -- queued job response with `job_id`, `status`, and `message`.
- `ScanJobResponse` -- ORM-backed job detail response with counters and lifecycle timestamps.
- `ScanJobListResponse` -- list wrapper for jobs.
- `ScanJobItemResponse` -- ORM-backed item response with status, linked `book_id`, and optional error/hash fields.
- `ScanJobItemListResponse` -- list wrapper for items.

### Reading Progress Schemas

Source: `backend/app/schemas/reading.py:10-75`

- `PdfLocator` -- page-based locator for PDF readers.
- `EpubLocator` -- CFI/progression-based locator for EPUB readers.
- `TxtLocator` -- line/column locator for TXT readers.
- `ReadingLocator` -- discriminated union across PDF/EPUB/TXT locator payloads.
- `ReadingProgressUpdate` -- request body for current-user progress upsert.
- `ReadingProgressResponse` -- ORM-backed response for one current-user progress row.
- `RecentReadingItem` -- joined book/progress summary for recent reading lists.
- `RecentReadingList` -- list wrapper for recent items.

### Note Schemas

Source: `backend/app/schemas/note.py:9-34`

- `BookNoteCreate` -- create payload for one current-user note.
- `BookNoteUpdate` -- partial update payload for one current-user note.
- `BookNoteResponse` -- ORM-backed response for one note row.
- `BookNoteListResponse` -- list wrapper for note rows.

## 4. Exports

`backend/app/schemas/__init__.py:1-24` re-exports:
- `User`, `UserCreate`, `UserLogin`, `Token`
- `Book`, `BookCreate`, `BookUpdate`, `BookList`
- `Category`, `CategoryCreate`
- `ScanDirectoryRequest`, `ScanFileRequest`, `ScanJobCreatedResponse`
- `ScanJobResponse`, `ScanJobListResponse`, `ScanJobItemResponse`, `ScanJobItemListResponse`
- `ReadingProgressUpdate`, `ReadingProgressResponse`, `RecentReadingItem`, `RecentReadingList`
- `BookNoteCreate`, `BookNoteUpdate`, `BookNoteResponse`, `BookNoteListResponse`

## 5. Current Gaps

- No `UserUpdate` schema.
- `BookUpdate` still covers only a subset of mutable ORM fields.
- `RecentReadingItem.file_format` is still serialized as a plain string from `backend/app/api/reading_progress.py:22-35` instead of reusing the book enum schema.
- `POST /scanner/jobs/{job_id}/retry-failed`, `POST /scanner/books/{book_id}/metadata-sync`, and `POST /scanner/books/{book_id}/extract-cover` still return ad-hoc dict payloads from `backend/app/api/scanner.py:105-116`, `:119-136`, and `:139-168`.

## 6. Response Coverage Notes

- `Book` response omits `file_path`, `publish_date`, `book_metadata`, `content_hash`, `indexed_at`, and relationships, but now includes `hash_status` and `metadata_synced_at` from `backend/app/schemas/book.py:27-46`.
- `User` response omits `avatar_url`, `last_login`, and `preferences`.
- `Category` response omits `parent` and `children` relationship data.
- `ScanJobResponse` omits `created_by` and any Celery dispatch identifier.
- `ScanJobItemResponse` omits file snapshot data such as `extension`, `size`, and `mtime`.
- ORM-backed response models use `from_attributes = True` in their inner `Config` classes.
