# Coding Conventions

## 1. Core Summary

The backend is a synchronous FastAPI application using SQLAlchemy ORM, Pydantic v2-style models, and direct route-to-DB patterns. Most business logic lives in `services/`, but routes still orchestrate DB reads/writes directly.

## 2. Source of Truth

- App entry: `backend/app/main.py:6-39`
- Configuration: `backend/app/core/config.py:5-43`
- DB/session: `backend/app/db/base.py:5-17`
- API dependencies: `backend/app/api/deps.py:8-40`
- Dependencies: `backend/requirements.txt:1-47`

## 3. Project Layout

```text
backend/app/
  main.py          # FastAPI app instance, middleware, root/health endpoints
  api/             # Route handlers
    router.py      # Router aggregation
    deps.py        # get_current_user / require_admin
  core/            # config, security
  db/              # engine, SessionLocal, Base
  models/          # SQLAlchemy ORM models
  schemas/         # Pydantic request/response models
  services/        # scanner, metadata, cover services
```

## 4. Naming Conventions

| Scope | Convention | Example |
|---|---|---|
| Files, functions, variables | `snake_case` | `get_books`, `scan_directory` |
| Classes | `PascalCase` | `BookScanner`, `ReadingProgress` |
| Enums | `PascalCase` class + `UPPER_CASE` members | `UserRole.ADMIN`, `ReadingStatus.NOT_STARTED` |
| Settings fields | `UPPER_CASE` | `SECRET_KEY`, `BOOKS_DIR` |
| DB tables | plural / descriptive snake_case | `books`, `reading_progress` |

## 5. Code Patterns

- **Config singleton:** Import `settings` from `backend/app/core/config.py:43`.
- **Sync DB access:** Use `db: Session = Depends(get_db)` from `backend/app/db/base.py:12-17`.
- **RBAC dependency:** Use `require_admin` from `backend/app/api/deps.py:34-40` for privileged routes.
- **Pydantic input extraction:** Current code uses `model_dump()` and `model_dump(exclude_unset=True)` in mutating handlers, e.g. `backend/app/api/books.py:66` and `:89`.
- **Route-first CRUD:** Routes generally query ORM models directly instead of using a repository abstraction.
- **Service boundaries:** Scanner, metadata, and cover operations live in `backend/app/services/`, but API routes still coordinate cross-service flow.
- **Logging style:** Services use the standard `logging` module, e.g. `backend/app/services/scanner_service.py:11`, `metadata_service.py:7`, `cover_service.py:9`.

## 6. Dependencies Actually in Use

| Category | Package |
|---|---|
| Framework | `fastapi`, `uvicorn` |
| ORM / migrations | `sqlalchemy`, `alembic`, `psycopg2-binary` |
| Auth | `python-jose`, `passlib`, `bcrypt` |
| Settings / validation | `pydantic`, `pydantic-settings`, `email-validator` |
| File / image | `ebookmeta`, `PyPDF2`, `Pillow`, `PyMuPDF` |
| HTTP | `httpx`, `requests` |
| Infra | `redis`, `celery`, `flower` |

## 7. Notes

- The runtime stack is sync-only even though some optional infra packages remain in `requirements.txt`.
- `BookCreate.file_format` is still a plain string in the schema layer, so routes that create books normalize it explicitly before ORM construction at `backend/app/api/books.py:66-68`.
- `.gitignore` now exists at project root and excludes env files, caches, and local storage paths.
