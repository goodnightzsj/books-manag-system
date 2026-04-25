#!/bin/bash
# All-in-one container entrypoint:
#   1. wait for postgres + redis (Python TCP probe; no client apt)
#   2. run alembic migrations as the `books` user
#   3. ensure admin user exists if ADMIN_PASSWORD is set
#   4. exec supervisord — runs nginx + uvicorn + worker + beat +
#      admin-web + reader-web in one container.
set -e

cd /app

wait_tcp() {
  python - <<PY
import socket, sys, time
host, port = "$1", $2
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
print(f"{host}:{port} not reachable", file=sys.stderr); sys.exit(1)
PY
}

echo "[entrypoint] waiting for postgres..."
wait_tcp postgres 5432

echo "[entrypoint] waiting for redis..."
wait_tcp redis 6379

echo "[entrypoint] running migrations..."
gosu books alembic upgrade head

echo "[entrypoint] ensuring admin..."
gosu books python -c "
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
        db.add(admin); db.commit()
        print('  admin created')
    elif admin:
        print('  admin exists')
    else:
        print('  ADMIN_PASSWORD empty -- skip admin bootstrap')
finally:
    db.close()
"

echo "[entrypoint] starting supervisord..."
exec /usr/bin/tini -- /usr/bin/supervisord -c /etc/supervisord.conf
