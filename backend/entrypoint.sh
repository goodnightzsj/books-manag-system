#!/bin/bash
set -e

echo "============================================"
echo "Books Management System - Starting Backend"
echo "============================================"
echo ""

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h postgres -U books_user -d books_db > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"
echo ""

# Wait for redis to be ready
echo "⏳ Waiting for Redis..."
python -c "
import redis
import time
import sys

max_retries = 30
for i in range(max_retries):
    try:
        r = redis.Redis(host='redis', port=6379, socket_connect_timeout=1)
        r.ping()
        break
    except:
        if i == max_retries - 1:
            print('❌ Redis connection failed after 30 attempts')
            sys.exit(1)
        time.sleep(1)
"
echo "✅ Redis is ready!"
echo ""

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head
echo "✅ Migrations completed!"
echo ""

# Check if admin user exists, if not create it
echo "👤 Checking admin user..."
python -c "
from app.db.base import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == 'admin').first()
    
    if not admin:
        print('Creating admin user...')
        admin = User(
            username='admin',
            email='admin@example.com',
            display_name='Administrator',
            password_hash=get_password_hash('admin123'),
            role='admin'  # Use string value directly instead of enum
        )
        db.add(admin)
        db.commit()
        print('✅ Admin user created successfully!')
        print('   Username: admin')
        print('   Password: admin123')
        print('   ⚠️  Please change the password after first login!')
    else:
        print('✅ Admin user already exists')
finally:
    db.close()
"
echo ""

# Start the application
echo "🚀 Starting FastAPI application..."
echo "📍 API will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
echo "============================================"
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
