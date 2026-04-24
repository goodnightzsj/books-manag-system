# Books Management System -- Documentation Index

Chinese-focused ebook library system. Backend creates persisted scan jobs for files inside the configured books directory, queues metadata and cover enrichment through Celery, reconciles stalled jobs through beat, serves book files with Range-aware streaming, and exposes a JWT-authenticated REST API with admin-gated write and scanner operations. Frontend is split into `admin-web` (Next.js console) and `reader-web` (Next.js PDF/EPUB/TXT reader); `apps/` provides Capacitor (mobile) and Tauri 2 (desktop) shells that reuse `reader-web`.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI 0.109 (sync mode) |
| ORM | SQLAlchemy 2.0 (sync engine) |
| Database | PostgreSQL 15+ |
| Cache | Redis 7+ |
| Auth | JWT (HS256) via python-jose, bcrypt via passlib |
| Migrations | Alembic (`backend/alembic/versions/001_initial.py`..`004_bookmarks_and_annotations.py`) |
| Containerization | Docker + `docker-compose.yml` at repo root |
| Frontend | Next.js 14 (App Router) + TypeScript (`frontend/admin-web`, `frontend/reader-web`) |
| Mobile / Desktop | Capacitor 6 (`apps/mobile-shell`), Tauri 2 (`apps/desktop-shell`) |
| Search (Phase 2) | Meilisearch adapter (`app/services/meilisearch_service.py`), enabled by `MEILI_URL` |
| Observability | `/metrics` (Prometheus), structured logging via `LOG_JSON` |
| Rate limiting | Redis token bucket at `app/core/rate_limit.py`, enabled by `RATE_LIMIT_PER_MINUTE` |

## Overview

- `overview/project-overview.md` -- Project identity, current capabilities, key paths, and the main remaining constraints.

## Architecture

- `architecture/api-architecture.md` -- FastAPI router layout, auth/RBAC split, job-backed scanner queue endpoints, Range-aware file access, and public file-cover access.
- `architecture/auth-architecture.md` -- JWT login flow, `get_current_user`, and `require_admin` enforcement.
- `architecture/data-models.md` -- Current ORM models, relationships, and the aligned schema baseline.
- `architecture/database-architecture.md` -- Sync engine/session setup, Alembic startup flow, and env-driven admin bootstrap.
- `architecture/recommendations-architecture.md` -- Five rule-based recommendation flows and their current limits.
- `architecture/services-architecture.md` -- Scanner job orchestration, search, reader-state, metadata merge, cover strategy, and Celery scan/hash/enrich/maintenance tasks.

## Guides

- `guides/deployment-guide.md` -- Docker and local startup, required env vars, `APP_ROLE=api|worker|beat`, startup sequence, and admin bootstrap behavior.
- `guides/scanning-workflow.md` -- Admin-only scan jobs, async metadata/cover enrichment, maintenance reconciliation, path rules, and error scenarios.

## Reference

- `reference/api-endpoints.md` -- All routed endpoints across 9 routers (auth, books, scanner, categories, reading-progress, notes, annotations, files, recommendations), including auth level, queued scanner actions, and file streaming behavior.
- `reference/coding-conventions.md` -- Project layout, sync FastAPI/SQLAlchemy patterns, and dependency usage.
- `reference/config-reference.md` -- `Settings` fields, defaults, and actual consumers.
- `reference/git-conventions.md` -- Observed git workflow, commit style, and `.gitignore` status.
- `reference/schemas-reference.md` -- Pydantic schema inventory and current schema-layer gaps.

## Quick-Start Pointers

**Understand the project:** Start with `overview/project-overview.md`, then `architecture/api-architecture.md`.

**Work on auth or permissions:** Read `architecture/auth-architecture.md` and `reference/api-endpoints.md`.

**Work on database behavior:** Read `architecture/database-architecture.md`, then `architecture/data-models.md`.

**Work on search, reading progress, or notes:** Read `architecture/api-architecture.md`, then `architecture/services-architecture.md` and `reference/schemas-reference.md`.

**Work on scanning, jobs, metadata, or cover tasks:** Read `guides/scanning-workflow.md`, then `architecture/services-architecture.md`.

**Deploy or configure:** Read `guides/deployment-guide.md` and `reference/config-reference.md`. The `docker-compose.yml` at the repo root boots `postgres / redis / api / worker / beat / nginx`; bare-metal templates live in `infra/deploy/systemd/`.

**Work on frontend:** `frontend/admin-web/` for the admin console (books / scanner / categories); `frontend/reader-web/` for the browser reader (PDF.js / epub.js / TXT + progress sync). Shells in `apps/` wrap the reader build for mobile / desktop.
