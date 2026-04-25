#!/usr/bin/env bash
# Standalone `docker run` deployment of books-manag-system, equivalent to
# the docker-compose stack but as 7 independent `docker run -d` commands.
#
# All persistent state lives on the external drive at /mnt/usb1-1/books/.
# The host nginx (already serving *.9962510.xyz) reverse-proxies to the
# loopback ports the containers expose on 127.0.0.1.
#
# Run this once after attaching the USB drive at /mnt/usb1-1 and copying
# any existing pg/redis data into the bind-mount targets.

set -euo pipefail

# --- ENV -------------------------------------------------------------
cd "$(dirname "$0")/../../.." && source .env

DATA=/mnt/usb1-1/books
NS="${IMAGE_NAMESPACE:-helloworldz1024}"
TAG="${IMAGE_TAG:-latest}"
NET=books

mkdir -p "$DATA"/{postgres-data,redis-data,books,uploads}

docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET"

# --- POSTGRES --------------------------------------------------------
docker rm -f books-postgres 2>/dev/null || true
docker run -d \
    --name books-postgres \
    --restart unless-stopped \
    --network "$NET" \
    -p 127.0.0.1:5433:5432 \
    -v "$DATA/postgres-data:/var/lib/postgresql/data" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    --health-cmd "pg_isready -U $POSTGRES_USER -d $POSTGRES_DB" \
    --health-interval 5s --health-timeout 3s --health-retries 10 \
    postgres:16-alpine

# --- REDIS -----------------------------------------------------------
docker rm -f books-redis 2>/dev/null || true
docker run -d \
    --name books-redis \
    --restart unless-stopped \
    --network "$NET" \
    -p 127.0.0.1:6380:6379 \
    -v "$DATA/redis-data:/data" \
    --health-cmd "redis-cli ping" \
    --health-interval 5s --health-timeout 3s --health-retries 10 \
    redis:7-alpine \
    redis-server --appendonly yes

# Wait for PG / Redis healthy before bringing up the app tier
echo "waiting for postgres + redis..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' books-postgres)" = healthy ] \
   && [ "$(docker inspect -f '{{.State.Health.Status}}' books-redis)" = healthy ]; do
    sleep 2
done

# --- BACKEND API -----------------------------------------------------
docker rm -f books-api 2>/dev/null || true
docker run -d \
    --name books-api \
    --restart unless-stopped \
    --network "$NET" \
    -p 127.0.0.1:8002:8000 \
    -v "$DATA/books:/app/books" \
    -v "$DATA/uploads:/app/uploads" \
    -e APP_ROLE=api \
    -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@books-postgres:5432/${POSTGRES_DB}" \
    -e REDIS_URL=redis://books-redis:6379/0 \
    -e CELERY_BROKER_URL=redis://books-redis:6379/0 \
    -e CELERY_RESULT_BACKEND=redis://books-redis:6379/1 \
    -e SECRET_KEY="$SECRET_KEY" \
    -e ADMIN_USERNAME="$ADMIN_USERNAME" \
    -e ADMIN_EMAIL="$ADMIN_EMAIL" \
    -e ADMIN_PASSWORD="$ADMIN_PASSWORD" \
    -e BOOKS_DIR=/app/books \
    -e UPLOADS_DIR=/app/uploads \
    -e ALLOWED_ORIGINS='["https://books.9962510.xyz"]' \
    "$NS/books-manag-system-backend:$TAG"

# --- WORKER ----------------------------------------------------------
docker rm -f books-worker 2>/dev/null || true
docker run -d \
    --name books-worker \
    --restart unless-stopped \
    --network "$NET" \
    -v "$DATA/books:/app/books" \
    -v "$DATA/uploads:/app/uploads" \
    -e APP_ROLE=worker \
    -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@books-postgres:5432/${POSTGRES_DB}" \
    -e REDIS_URL=redis://books-redis:6379/0 \
    -e CELERY_BROKER_URL=redis://books-redis:6379/0 \
    -e CELERY_RESULT_BACKEND=redis://books-redis:6379/1 \
    -e SECRET_KEY="$SECRET_KEY" \
    -e BOOKS_DIR=/app/books \
    -e UPLOADS_DIR=/app/uploads \
    -e CELERY_QUEUES=scan,enrich,maintenance \
    "$NS/books-manag-system-backend:$TAG"

# --- BEAT ------------------------------------------------------------
docker rm -f books-beat 2>/dev/null || true
docker run -d \
    --name books-beat \
    --restart unless-stopped \
    --network "$NET" \
    -e APP_ROLE=beat \
    -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@books-postgres:5432/${POSTGRES_DB}" \
    -e REDIS_URL=redis://books-redis:6379/0 \
    -e CELERY_BROKER_URL=redis://books-redis:6379/0 \
    -e CELERY_RESULT_BACKEND=redis://books-redis:6379/1 \
    -e SECRET_KEY="$SECRET_KEY" \
    "$NS/books-manag-system-backend:$TAG"

# --- ADMIN WEB -------------------------------------------------------
docker rm -f books-admin-web 2>/dev/null || true
docker run -d \
    --name books-admin-web \
    --restart unless-stopped \
    --network "$NET" \
    -p 127.0.0.1:3010:3000 \
    -e NEXT_PUBLIC_API_BASE=https://books.9962510.xyz \
    "$NS/books-manag-system-admin-web:$TAG"

# --- READER WEB ------------------------------------------------------
docker rm -f books-reader-web 2>/dev/null || true
docker run -d \
    --name books-reader-web \
    --restart unless-stopped \
    --network "$NET" \
    -p 127.0.0.1:3011:3001 \
    -e NEXT_PUBLIC_API_BASE=https://books.9962510.xyz \
    "$NS/books-manag-system-reader-web:$TAG"

echo
docker ps --filter name=books- --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
