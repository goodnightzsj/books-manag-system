#!/bin/bash
set -e

ROLE="${APP_ROLE:-api}"

# Pure-Python TCP probes — no `postgresql-client` apt package needed.
# Hostnames `postgres` and `redis` come from the docker network.
wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  python - <<'PY'
import os, socket, sys, time
host = "postgres"
port = 5432
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("PostgreSQL not reachable after 60s", file=sys.stderr)
sys.exit(1)
PY
  echo "PostgreSQL is ready"
}

wait_for_redis() {
  echo "Waiting for Redis..."
  python - <<'PY'
import socket, sys, time
host = "redis"
port = 6379
for _ in range(30):
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Redis not reachable after 30s", file=sys.stderr)
sys.exit(1)
PY
  echo "Redis is ready"
}

run_migrations() {
  echo "Running database migrations..."
  alembic upgrade head
}

ensure_admin() {
  echo "Checking admin user..."
  python -c "
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import SessionLocal
from app.models.user import User, UserRole

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if not admin and settings.ADMIN_PASSWORD:
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            display_name='Administrator',
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print('Admin user created')
    elif admin:
        print('Admin user already exists')
    else:
        print('ADMIN_PASSWORD not set; skipping admin bootstrap')
finally:
    db.close()
"
}

start_api() {
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
}

start_worker() {
  exec celery -A app.celery_app.celery_app worker -Q "${CELERY_QUEUES:-scan,enrich,maintenance}" --loglevel INFO
}

start_beat() {
  exec celery -A app.celery_app.celery_app beat --loglevel INFO
}

wait_for_postgres
wait_for_redis

if [ "$ROLE" = "api" ]; then
  run_migrations
  ensure_admin
  start_api
elif [ "$ROLE" = "worker" ]; then
  start_worker
elif [ "$ROLE" = "beat" ]; then
  start_beat
else
  echo "Unsupported APP_ROLE: $ROLE"
  exit 1
fi
