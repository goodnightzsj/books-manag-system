# How to Deploy the Books Management System

This guide covers the current Docker-oriented backend deployment flow.

## Prerequisites

Required settings come from `backend/app/core/config.py:6-46`.

### Required

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`

### Optional but operationally important

- `ADMIN_USERNAME` -- defaults to `admin`
- `ADMIN_EMAIL` -- defaults to `admin@example.com`
- `ADMIN_PASSWORD` -- empty by default; required only if you want automatic admin bootstrap
- `BOOKS_DIR` -- defaults to `/app/books`
- `UPLOADS_DIR` -- defaults to `/app/uploads`

## Docker Deployment

1. **Build the image.** Main image definition: `backend/Dockerfile:1-55`. It installs build deps temporarily, runtime packages (`libpq5`, `libmagic1`, `postgresql-client`), installs Python dependencies, then purges build tools. An alternative image exists at `backend/Dockerfile.optimized:1-35`.
2. **Provide service discovery for Postgres and Redis.** The startup script still checks `postgres` and `redis` directly at `backend/entrypoint.sh:6-31`.
3. **Mount persistent directories.** The image creates `/app/books` and `/app/uploads` at `backend/Dockerfile:46-47`.
4. **Expose port 8000 for the API role.** The container listens on port 8000 and the Dockerfile exposes it at `backend/Dockerfile:53`.
5. **Choose the runtime role with `APP_ROLE`.** `backend/entrypoint.sh:4-95` supports `api`, `worker`, and `beat`.
6. **Startup sequence:** `backend/entrypoint.sh:82-95`
   - All roles wait for PostgreSQL and Redis readiness first.
   - `APP_ROLE=api` runs `alembic upgrade head`, optionally bootstraps the admin account, then starts uvicorn at `backend/entrypoint.sh:85-88`.
   - `APP_ROLE=worker` starts Celery worker processes and defaults `CELERY_QUEUES` to `scan,enrich,maintenance` at `backend/entrypoint.sh:74-76`.
   - `APP_ROLE=beat` starts Celery beat at `backend/entrypoint.sh:78-79`.
7. **Verify service health.** Call `GET /health` from `backend/app/main.py:37-39` against the API role.

## Local Development Startup

1. Install dependencies from `backend/requirements.txt`.
2. Create `backend/.env` with at least `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`.
3. Run `alembic upgrade head` from `backend/` before starting the API.
4. Start the API with `uvicorn app.main:app --reload` if you want local autoreload.
5. Start a Celery worker for `scan`, `enrich`, and `maintenance` queues if you need scan, metadata, cover, or reconciliation jobs.
6. Start Celery beat as a separate process if you want scheduled stalled-job reconciliation.

## Admin Bootstrap Behavior

There is no fixed default password anymore.

- `backend/entrypoint.sh:49-64` only creates the admin if `ADMIN_PASSWORD` is non-empty.
- `backend/scripts/create_admin.py:21-37` follows the same rule for manual bootstrap.
- Only `APP_ROLE=api` runs the bootstrap path at `backend/entrypoint.sh:85-88`.
- If `ADMIN_PASSWORD` is empty, startup logs a skip message and continues.

## Current Constraints

- **No committed compose file:** The repo still does not include `docker-compose.yml`.
- **Hostnames are hardcoded in readiness checks:** `postgres` and `redis` are embedded in `backend/entrypoint.sh:6-31`.
- **Role split is operationally required for async features:** metadata sync, cover sync, and maintenance reconciliation depend on worker and beat processes in addition to the API role.
- **Redis is checked but not actively used by the app layer:** `REDIS_URL` is required by config, but current runtime queue behavior is driven by `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.
- **Legacy test script uses environment variables:** `backend/test_api.py:10-12` and `:147-153` read `ADMIN_USERNAME` and `ADMIN_PASSWORD` from the environment.
