#!/bin/bash
set -e

ROLE="${APP_ROLE:-api}"

wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  while ! pg_isready -h postgres -U books_user -d books_db > /dev/null 2>&1; do
    sleep 1
  done
  echo "PostgreSQL is ready"
}

wait_for_redis() {
  echo "Waiting for Redis..."
  python -c "
import redis
import sys
import time

for i in range(30):
    try:
        redis.Redis(host='redis', port=6379, socket_connect_timeout=1).ping()
        break
    except Exception:
        if i == 29:
            print('Redis connection failed after 30 attempts')
            sys.exit(1)
        time.sleep(1)
"
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
