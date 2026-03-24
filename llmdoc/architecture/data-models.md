# Architecture of Data Models

## 1. Identity

- **What it is:** The SQLAlchemy ORM layer for users, books, categories, reading progress, scan jobs, and notes.
- **Purpose:** Define the relational schema, enum domains, job state, and object relationships used by the API and services layer.

## 2. Core Components

- `backend/app/db/base.py:5-17` -- Defines the shared `Base`, engine, and `SessionLocal`.
- `backend/app/models/book.py:9-82` -- `FileFormat`, `HashStatus`, `book_category`, `Book`, and `Category`.
- `backend/app/models/user.py:10-30` -- `UserRole` and `User`.
- `backend/app/models/reading.py:10-41` -- `ReadingStatus` and `ReadingProgress` with per-user/per-book uniqueness.
- `backend/app/models/scan_job.py:12-74` -- `ScanJobType`, `ScanJobStatus`, `ScanItemStatus`, `ScanJob`, and `ScanJobItem`.
- `backend/app/models/note.py:11-23` -- `BookNote`.
- `backend/app/models/__init__.py:1-7` -- Re-exports `User`, `Book`, `Category`, `ReadingProgress`, `ScanJob`, `ScanJobItem`, and `BookNote`.
- `backend/alembic/versions/001_initial.py:19-106` -- Original schema baseline.
- `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:1-143` -- Batch A schema extension.

## 3. Model Details

**Book** -- `backend/app/models/book.py:32-68`
- UUID primary key.
- Indexed lookup fields: `title`, `author`, `isbn`, `content_hash`.
- File fields: `file_path`, `file_format`, `file_size`, `file_mtime`.
- Hash / indexing fields: `content_hash`, `hash_algorithm`, `hash_status`, `hash_error`, `search_vector`.
- Metadata fields: `subtitle`, `publisher`, `publish_date`, `description`, `cover_url`, `language`, `page_count`, `rating`, `rating_count`, `tags`, `book_metadata`, `source_provider`, `metadata_synced_at`.
- Timestamps: `created_at`, `updated_at`, `indexed_at`.
- Relationships: many-to-many with `Category`, one-to-many with `ReadingProgress`, one-to-many with `BookNote`.

**Category** -- `backend/app/models/book.py:54-66`
- UUID primary key.
- `name` is unique and indexed.
- Optional `parent_id` enables a self-referential tree.
- Relationships: `books`, `parent`, and `children`.
- The self-reference is anchored with `remote_side=[id]` at `backend/app/models/book.py:65-66`.

**book_category** -- `backend/app/models/book.py:18-23`
- Association table for the book/category many-to-many relation.
- Composite primary key: `book_id`, `category_id`.

**User** -- `backend/app/models/user.py:15-30`
- UUID primary key.
- Unique indexed identifiers: `username`, `email`.
- Authentication fields: `password_hash`, `last_login`.
- Profile fields: `display_name`, `avatar_url`, `preferences`.
- `role` is a SQLAlchemy enum over `UserRole.ADMIN` and `UserRole.USER`.
- Relationship: one-to-many `reading_progress`.

**ReadingProgress** -- `backend/app/models/reading.py:17-41`
- UUID primary key.
- Foreign keys: `user_id`, `book_id`.
- Enforces `UNIQUE (user_id, book_id)` in the ORM and migration at `backend/app/models/reading.py:19-21` and `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:92-93`.
- Progress fields: `current_page`, `total_pages`, `progress_percent`, `status`, `locator`, `last_read_at`.
- Lifecycle fields: `started_at`, `finished_at`, `created_at`, `updated_at`.
- Extra data: legacy `notes`, `bookmarks`.
- Relationships: `user`, `book`.

**ScanJob / ScanJobItem** -- `backend/app/models/scan_job.py:37-74`
- `ScanJob` stores job type, state, normalized path, aggregate counters, creator, and lifecycle timestamps.
- `ScanJobItem` stores per-file status, resolved path, format, linked `book_id`, and optional detected hash.
- Relationship: one `ScanJob` to many `ScanJobItem` rows.

**BookNote** -- `backend/app/models/note.py:11-23`
- UUID primary key.
- Foreign keys: `user_id`, `book_id`.
- Stores optional `locator`, required `note_text`, and lifecycle timestamps.
- Relationship: many notes per `Book`.

## 4. Relationship Map

- **Book <-> Category:** Many-to-many through `book_category`.
- **User -> ReadingProgress:** One-to-many with cascade `all, delete-orphan` at `backend/app/models/user.py:29-30`.
- **Book -> ReadingProgress:** One-to-many with cascade `all, delete-orphan` at `backend/app/models/book.py:66-68`.
- **Book -> BookNote:** One-to-many with cascade `all, delete-orphan` at `backend/app/models/book.py:66-68` and `backend/app/models/note.py:22-23`.
- **ScanJob -> ScanJobItem:** One-to-many with cascade `all, delete-orphan` at `backend/app/models/scan_job.py:56`.
- **Category -> Category:** Self-reference through `parent_id`.

## 5. Current Schema Status

- Batch A extends the original baseline through `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:19-109`.
- The ORM and migration are aligned for the main Batch A additions:
  - `books` now carry hash/search fields at `backend/app/models/book.py:47-60` and `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:33-48`, and those hash fields are now actively driven by `backend/app/services/book_ingest_service.py:30-95` and `backend/app/tasks/hash_tasks.py:11-43`.
  - `scan_jobs` / `scan_job_items` exist in both layers at `backend/app/models/scan_job.py:37-75` and `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:50-90`, with `scan_job_items.detected_hash` now backfilled from `backend/app/services/book_ingest_service.py:102-106`.
  - `reading_progress` now includes `locator` and enforces `UNIQUE (user_id, book_id)` at `backend/app/models/reading.py:19-30` and `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:92-93`.
  - `book_notes` exists in both layers at `backend/app/models/note.py:11-23` and `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py:95-108`.
- Earlier enum/value alignments also remain intact:
  - `users.role` matches between `backend/app/models/user.py:10-25` and `backend/alembic/versions/001_initial.py:28`.
  - `books.file_format` uses lowercase enum values in both `backend/app/models/book.py:9-15` and `backend/alembic/versions/001_initial.py:61`.

## 6. Remaining Model-Level Gaps

- `Book.tags`, `Book.book_metadata`, `User.preferences`, and `ReadingProgress.bookmarks` still use generic `JSON`, not PostgreSQL `JSONB`; see `backend/app/models/book.py:56-57`, `backend/app/models/user.py:25`, and `backend/app/models/reading.py:35`.
- Initial ingest still uses file snapshot checks to decide whether rehash is needed, but duplicate identity now converges on `content_hash` after `backend/app/tasks/hash_tasks.py:11-43` calls `backend/app/services/book_ingest_service.py:97-174`; the pre-hash decision path still starts from `backend/app/services/hash_service.py:20-45` and `backend/app/services/book_ingest_service.py:30-95`.
- There is still no Pydantic schema layer for `ReadingProgress` or `BookNote`; scanner is the only new Batch A schema surface at `backend/app/schemas/scanner.py:13-70`.

## 7. Design Rationale

- `book_metadata` is kept as a separate field name instead of `metadata` to avoid SQLAlchemy reserved-name conflicts at `backend/app/models/book.py:45`.
- Enums are defined as `str, enum.Enum` subclasses so API responses serialize cleanly while the DB still stores constrained values.
- Timestamps rely on `datetime.utcnow` defaults and `onupdate` hooks instead of DB-managed triggers.
