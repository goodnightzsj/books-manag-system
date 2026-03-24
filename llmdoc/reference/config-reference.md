# Configuration Reference

## 1. Core Summary

All runtime settings are defined in `backend/app/core/config.py:6-46` via one `Settings(BaseSettings)` class. A module-level `settings` singleton is instantiated at `backend/app/core/config.py:46`. Configuration is case-sensitive and loaded from `.env` through the inner `Config` at `backend/app/core/config.py:41-43`.

## 2. Source of Truth

- **Primary code:** `backend/app/core/config.py:6-46`
- **Consumers:** `backend/app/main.py`, `backend/app/db/base.py`, `backend/app/core/security.py`, `backend/app/celery_app.py`, `backend/app/tasks/metadata_tasks.py`, `backend/app/tasks/maintenance_tasks.py`, `backend/app/api/files.py`, `backend/app/services/file_access_service.py`, `backend/app/services/task_dispatch_service.py`, `backend/entrypoint.sh`, `backend/scripts/create_admin.py`

## 3. Settings Summary

### Required

| Setting | Type | Consumed by |
|---|---|---|
| `DATABASE_URL` | `str` | `backend/app/db/base.py:5` and `backend/alembic/env.py:19` |
| `REDIS_URL` | `str` | Required by settings import, but not directly consumed by current Python app modules |
| `SECRET_KEY` | `str` | `backend/app/core/security.py:20-28` |

### Optional

| Setting | Type | Default | Consumed by |
|---|---|---|---|
| `APP_NAME` | `str` | `"Books Management System"` | `backend/app/main.py:6-9` |
| `DEBUG` | `bool` | `False` | `backend/app/main.py:6-9` |
| `API_V1_PREFIX` | `str` | `"/api/v1"` | `backend/app/main.py:26-27` |
| `CELERY_BROKER_URL` | `str` | `"redis://redis:6379/0"` | `backend/app/celery_app.py:7-10` |
| `CELERY_RESULT_BACKEND` | `str` | `"redis://redis:6379/1"` | `backend/app/celery_app.py:7-10` |
| `CELERY_DEFAULT_QUEUE` | `str` | `"scan"` | `backend/app/celery_app.py:13-19` |
| `BOOKS_SCAN_QUEUE` | `str` | `"scan"` | `backend/app/celery_app.py:15-18` and `backend/app/services/task_dispatch_service.py:8-29` |
| `BOOKS_ENRICH_QUEUE` | `str` | `"enrich"` | `backend/app/celery_app.py:15-18` and `backend/app/services/task_dispatch_service.py:31-58` |
| `BOOKS_MAINTENANCE_QUEUE` | `str` | `"maintenance"` | `backend/app/celery_app.py:15-18` and `backend/app/services/task_dispatch_service.py:60-65` |
| `SCAN_JOB_STALLED_SECONDS` | `int` | `1800` | `backend/app/tasks/maintenance_tasks.py:14-16` |
| `SCAN_ITEM_STALLED_SECONDS` | `int` | `1800` | `backend/app/tasks/maintenance_tasks.py:14-16` |
| `MAINTENANCE_RECONCILE_INTERVAL_SECONDS` | `int` | `300` | `backend/app/celery_app.py:27-32` |
| `ALGORITHM` | `str` | `"HS256"` | `backend/app/core/security.py:23,28` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `30` | `backend/app/core/security.py:20` |
| `ADMIN_USERNAME` | `str` | `"admin"` | `backend/entrypoint.sh:49-52` and `backend/scripts/create_admin.py:16,26` |
| `ADMIN_EMAIL` | `str` | `"admin@example.com"` | `backend/entrypoint.sh:53` and `backend/scripts/create_admin.py:27` |
| `ADMIN_PASSWORD` | `str` | `""` | `backend/entrypoint.sh:50,55,64` and `backend/scripts/create_admin.py:21,29` |
| `ALLOWED_ORIGINS` | `List[str]` | `["http://localhost:3000", "http://localhost:19006"]` | `backend/app/main.py:14-23` |
| `BOOKS_DIR` | `str` | `"/app/books"` | `backend/app/services/file_access_service.py:36-59` |
| `UPLOADS_DIR` | `str` | `"/app/uploads"` | `backend/app/tasks/cover_tasks.py:23-28` and `backend/app/api/files.py:38-45` |
| `MAX_UPLOAD_SIZE` | `int` | `104857600` | Declared only; no active consumer in current code |
| `DOUBAN_API_URL` | `str` | `"https://douban.uieee.com"` | Declared in settings and used as the default provider URL in `backend/app/services/metadata_service.py:110-145` |
| `GOOGLE_BOOKS_API_KEY` | `str` | `""` | `backend/app/tasks/metadata_tasks.py:18-21` |

## 4. Loading Rules

- `.env` is loaded relative to the backend runtime working directory through `env_file = ".env"`.
- Field names are case-sensitive because `case_sensitive = True` is set at `backend/app/core/config.py:43`.
- Missing required fields cause settings initialization to fail during import.

## 5. Notes

- `ALLOWED_ORIGINS` supports both a native list and a comma-separated string because `backend/app/main.py:14-16` normalizes string input.
- Celery now imports scan, hash, metadata, cover, and maintenance tasks, and beat schedules stalled-job reconciliation through `backend/app/celery_app.py:20-33`.
- `APP_ROLE` and `CELERY_QUEUES` are shell-level deployment inputs read only by `backend/entrypoint.sh:4` and `:75`; they are not part of the Pydantic `Settings` surface.
- `REDIS_URL` remains part of the required configuration surface, but current Python runtime behavior is driven by `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` instead.
