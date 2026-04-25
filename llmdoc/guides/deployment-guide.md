# How to Deploy the Books Management System

Three supported deployment paths: **Docker Compose** (recommended),
**bare-metal systemd** (VPS / Ubuntu / CentOS), and **local dev**.

The canonical public hostname is **`books.9962510.xyz`**:

- `/` -- reader-web
- `/admin/` -- admin-web
- `/api/v1/` -- backend API
- `/uploads/` -- static covers (read-only)
- `/docs`, `/openapi.json` -- API docs
- `/health`, `/metrics` -- ops endpoints

`infra/docker/nginx/conf.d/api.conf` already sets `server_name
books.9962510.xyz` and enforces HSTS + modern TLS ciphers. For TLS
bootstrap (Caddy / certbot / Cloudflare), see `infra/deploy/cert/README.md`.

## Prerequisites

Runtime settings live in `backend/app/core/config.py`. Full key
reference: `llmdoc/reference/config-reference.md`.

### Required

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`

### Operationally important

- `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` -- empty password
  skips admin bootstrap.
- `BOOKS_DIR`, `UPLOADS_DIR` -- mount points.
- `MEILI_URL` / `MEILI_MASTER_KEY` -- optional Phase-2 search; empty
  falls back to PostgreSQL FTS exclusively.
- `RATE_LIMIT_PER_MINUTE` -- 0 disables the Redis rate limiter.
- `CACHE_TTL_SECONDS` -- 0 disables the recommendation / hot-read cache.
- `METRICS_ENABLED`, `LOG_JSON`, `LOG_LEVEL` -- observability toggles.

## Option 1: Docker Compose (recommended)

The repo ships `docker-compose.yml` at the root, wiring
`postgres / redis / api / worker / beat / nginx` with healthchecks and
persistent volumes. Supporting templates live in `infra/docker/nginx/`.

```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD, SECRET_KEY, ADMIN_PASSWORD at minimum
mkdir -p books uploads
docker compose up -d --build
docker compose logs -f api
# first run creates admin via entrypoint if ADMIN_PASSWORD is set
curl -s http://localhost/health
```

The nginx service listens on `HTTP_PORT` (default `80`) and proxies
`/api/*`, `/docs`, `/openapi.json`, `/health` to the `api` container;
static uploads are served read-only from `/uploads/`.

To opt into Meilisearch, add a `meilisearch` service and set
`MEILI_URL=http://meilisearch:7700` in `.env` -- the adapter at
`backend/app/services/meilisearch_service.py` activates automatically.

## Option 2: Bare-metal (systemd)

Templates live in `infra/deploy/systemd/`:

- `books-api.service`, `books-worker.service`, `books-beat.service`
- `books.env.example` -- `EnvironmentFile` template
- `README.md` -- step-by-step bootstrap

Summary:

```bash
sudo useradd --system --home /var/lib/books --shell /usr/sbin/nologin books
sudo mkdir -p /opt/books-manag-system /var/lib/books/{books,uploads} /etc/books
# clone + venv install
sudo cp infra/deploy/systemd/*.service /etc/systemd/system/
sudo cp infra/deploy/systemd/books.env.example /etc/books/books.env
sudo systemctl daemon-reload
sudo systemctl enable --now books-api books-worker books-beat
```

Front with an existing nginx or use `infra/docker/nginx/conf.d/api.conf`
as a starting point (swap `upstream` target to `127.0.0.1:8000`).

## Option 3: Local development

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# in other terminals:
celery -A app.celery_app.celery_app worker -Q scan,enrich,maintenance
celery -A app.celery_app.celery_app beat
```

For the frontend during dev:

```bash
cd frontend/admin-web && npm install && npm run dev     # :3000
cd frontend/reader-web && npm install && npm run dev    # :3001
```

Both Next.js apps proxy `/api/*` to `NEXT_PUBLIC_API_BASE` (default
`http://localhost:8000`), so CORS is not required locally.

## APP_ROLE matrix

`backend/entrypoint.sh` dispatches on `APP_ROLE`:

| Role | Behavior |
|---|---|
| `api` | waits for PG+Redis, runs `alembic upgrade head`, admin bootstrap, `uvicorn` |
| `worker` | starts Celery worker on `CELERY_QUEUES` (default `scan,enrich,maintenance`) |
| `beat` | starts Celery beat for scheduled stalled-job reconciliation |

## Admin bootstrap

- `backend/entrypoint.sh` only creates the admin user when
  `ADMIN_PASSWORD` is non-empty; empty logs a skip.
- `backend/scripts/create_admin.py` does the same for manual runs.
- Only the `api` role triggers bootstrap.

## Observability endpoints

- `GET /health` -- liveness
- `GET /metrics` -- Prometheus scrape target (enabled by
  `METRICS_ENABLED=true`, default true)
- `LOG_JSON=true` -- switches stdout to JSON for log shippers.

## Release flow (GitHub Actions)

Tag-only pipelines live under `.github/workflows/`:

| Workflow | Trigger | Output |
|---|---|---|
| `docker-publish.yml` | `tags: v*` | 3 multi-arch images (`backend`, `admin-web`, `reader-web`) -> Docker Hub + `docker-images.txt` asset |
| `desktop-release.yml` | `tags: v*` | Tauri bundles for win-x64 / mac-arm64 / mac-x64 / linux-x64 |
| `android-release.yml` | `tags: v*` | Capacitor APK / AAB (signed when keystore secret present, debug otherwise) |
| `ios-release.yml` | `tags: v*` | Capacitor IPA (signed) or Simulator `.app.tar.gz` (fallback) |
| `ci.yml` | push / PR to `main` | unit tests + typecheck only, no artifacts |

All four release workflows attach assets to the **same** unified GitHub Release for the tag (shared `body_path: .github/RELEASE_BODY.md`).

### Required repo settings

| Kind | Name | Notes |
|---|---|---|
| Variable | `DOCKERHUB_USERNAME` | Preferred. Falls back to `secrets.DOCKERHUB_USERNAME`. |
| Variable | `DOCKERHUB_NAMESPACE` | Optional override; defaults to username. |
| Secret | `DOCKERHUB_TOKEN` | Personal Access Token with **Read & Write** on the three target repos. |
| Secret | `ANDROID_KEYSTORE_*` | Optional; without these the workflow ships an unsigned debug APK. |
| Secret | `IOS_*` / `APPLE_*` | Optional; without these the workflow ships a Simulator `.app.tar.gz`. |
| Secret | `APPLE_SIGNING_IDENTITY`, `WINDOWS_CERTIFICATE`, `TAURI_SIGNING_PRIVATE_KEY` | Optional desktop signing. |

### Cutting a release

```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

Kicks off all four workflows in parallel; each uploads to the same draft release. Review and publish from the GitHub UI when all jobs report green.

### Why tag-only

Every-commit Docker builds are intentionally avoided to:

1. Stay under Docker Hub rate limits.
2. Avoid `:main` images that operators are tempted to pin in production.
3. Keep `latest` synonymous with the most recent reviewed point in history.

`mirror.gcr.io` is configured in the buildx step to bypass anonymous pull rate limits for base images.

## Historical notes

- Earlier revisions had no compose file; as of `docker-compose.yml`
  + `docker-compose.prod.yml` at the repo root this is no longer the case.
- `entrypoint.sh` still hardcodes `postgres` and `redis` as readiness
  hostnames -- aligns with compose service names. For bare-metal put
  entries in `/etc/hosts` or edit the script.
