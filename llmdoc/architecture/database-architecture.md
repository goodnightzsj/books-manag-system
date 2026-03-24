# Database Architecture

## 1. Identity

- **What it is:** The synchronous SQLAlchemy + PostgreSQL persistence layer with Alembic migrations.
- **Purpose:** Provide ORM metadata, request-scoped sessions, and a single migration-driven schema creation path.

## 2. Core Components

- `backend/app/db/base.py:5-17` -- Creates the engine from `DATABASE_URL`, defines `SessionLocal`, `Base`, and `get_db()`.
- `backend/app/core/config.py:11-25` -- Declares `DATABASE_URL` and admin-bootstrap settings.
- `backend/app/models/__init__.py:1-4` -- Import surface used by Alembic to register ORM models.
- `backend/alembic/env.py:11-26` -- Imports `app.models`, injects `settings.DATABASE_URL`, and sets `target_metadata = Base.metadata`.
- `backend/alembic/versions/001_initial.py:19-126` -- Creates `users`, `categories`, `books`, `book_categories`, and `reading_progress`.
- `backend/entrypoint.sh:39-87` -- Runs migrations before starting the API and optionally bootstraps the admin user.
- `backend/app/main.py:6-39` -- Builds the FastAPI app; it no longer creates tables directly.

## 3. Execution Flow

### 3.1 Schema Creation and Startup

- **1. Container start:** `backend/entrypoint.sh:39-41` runs `alembic upgrade head`.
- **2. Alembic bootstrap:** `backend/alembic/env.py:11-26` imports `app.models` and points Alembic at `Base.metadata`.
- **3. Migration execution:** `backend/alembic/versions/001_initial.py:19-106` creates the five application tables and enum types.
- **4. App startup:** `backend/app/main.py:6-27` starts FastAPI and mounts routers. There is no secondary `create_all()` path anymore.

### 3.2 Session Lifecycle

- **1. Dependency injection:** Routes declare `db: Session = Depends(get_db)`.
- **2. Session open:** `backend/app/db/base.py:12-13` instantiates `SessionLocal()`.
- **3. Yield to handler:** `backend/app/db/base.py:14-15` passes the session into the route.
- **4. Cleanup:** `backend/app/db/base.py:16-17` always closes the session.

### 3.3 Admin Bootstrap

- **1. Read config:** `backend/entrypoint.sh:47-52` imports `settings.ADMIN_USERNAME`, `settings.ADMIN_EMAIL`, and `settings.ADMIN_PASSWORD`.
- **2. Query existing admin:** `backend/entrypoint.sh:55` checks for the configured username.
- **3. Conditional create:** `backend/entrypoint.sh:57-69` creates the user only when it does not already exist and `ADMIN_PASSWORD` is non-empty.
- **4. Safe skip:** `backend/entrypoint.sh:70-73` leaves the DB unchanged when the admin already exists or no bootstrap password is configured.

## 4. Schema Inventory

| Table | ORM | Key Notes |
|---|---|---|
| `users` | `User` | Unique `username` and `email`, enum `role`, JSON `preferences` |
| `categories` | `Category` | Unique indexed `name`, optional `parent_id` self-reference |
| `books` | `Book` | Indexed `title`/`author`, unique `isbn`, enum `file_format` |
| `book_categories` | `book_category` | Many-to-many join table with composite PK |
| `reading_progress` | `ReadingProgress` | Progress metrics, timestamps, notes, bookmarks |

## 5. Current Schema Status

- The migration and ORM are currently aligned for `users.role`, `books.file_format`, and `reading_progress`; compare `backend/app/models/user.py:24`, `backend/app/models/book.py:38`, and `backend/app/models/reading.py:20-33` with `backend/alembic/versions/001_initial.py:28`, `:61`, and `:88-102`.
- The database layer is now Alembic-first. `backend/app/main.py` does not call `Base.metadata.create_all()`.
- The project still has a single migration revision (`001`). Any future schema change requires either editing the baseline before first deployment or adding new Alembic revisions.

## 6. Design Notes and Constraints

- The stack is sync-only. `backend/app/db/base.py:5-17` uses `create_engine`, not an async engine.
- `entrypoint.sh` still hardcodes readiness checks against hosts `postgres` and `redis` at `backend/entrypoint.sh:11` and `:27`.
- `REDIS_URL` exists in settings, but current Python application code does not initialize a Redis client from it.
- The repo still has no committed `docker-compose.yml`, so the surrounding runtime topology must supply the expected service names.
