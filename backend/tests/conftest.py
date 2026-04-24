"""Shared pytest fixtures for integration tests.

These tests require SQLAlchemy + FastAPI TestClient to be importable.
If unavailable, individual test modules should mark themselves as skipped.
SQLite is used as an in-memory substitute so the suite can run without
a PostgreSQL instance; PG-specific features (TSVECTOR, pg_trgm) are
tolerated by skip-guards inside the test cases themselves.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-please-change")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

try:
    import pytest  # noqa: F401
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore
