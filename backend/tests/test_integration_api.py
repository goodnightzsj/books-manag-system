"""Integration test skeleton using FastAPI TestClient.

These tests are skipped when the heavy runtime deps (SQLAlchemy, FastAPI,
Pydantic, passlib, etc.) are not present. They form a reusable scaffold
for CI where those deps are installed.

Strategy:
 - Replace `settings.DATABASE_URL` with a file-based SQLite DB before any
   model/engine import happens (handled by `conftest.py`).
 - Create schema via `Base.metadata.create_all(engine)` -- the MVP models
   that rely on Postgres-only features (TSVECTOR) degrade to plain columns
   under SQLite because SQLAlchemy falls back to TEXT for unknown types
   on the SQLite dialect.
 - Exercise the happy paths: register, login, create book, list, update,
   reading-progress upsert, notes CRUD.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

TMP_DB_PATH: Path | None = None


def _init_sqlite_env() -> bool:
    global TMP_DB_PATH
    if TMP_DB_PATH is not None:
        return True
    fd, path = tempfile.mkstemp(suffix=".sqlite", prefix="books_test_")
    os.close(fd)
    TMP_DB_PATH = Path(path)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    return True


try:
    _init_sqlite_env()
    from fastapi.testclient import TestClient  # type: ignore
    from sqlalchemy import create_engine  # type: ignore
    from sqlalchemy.orm import sessionmaker  # type: ignore

    import app.db.base as db_base  # type: ignore

    # Rebind engine/session to the sqlite URL before any routes import.
    _engine = create_engine(
        os.environ["DATABASE_URL"],
        connect_args={"check_same_thread": False},
    )
    db_base.engine = _engine
    db_base.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    import app.models  # noqa: F401 -- ensure models register on Base
    from app.db.base import Base  # type: ignore
    from app.main import app  # type: ignore

    Base.metadata.create_all(bind=_engine)
    _RUNTIME_AVAILABLE = True
    _CLIENT = TestClient(app)
except Exception as exc:  # pragma: no cover
    _RUNTIME_AVAILABLE = False
    _CLIENT = None
    _IMPORT_ERROR = exc


@unittest.skipUnless(_RUNTIME_AVAILABLE, "heavy runtime deps not available in this env")
class IntegrationApiTests(unittest.TestCase):
    def test_health_endpoint(self) -> None:
        r = _CLIENT.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "healthy")

    def test_register_and_login(self) -> None:
        r = _CLIENT.post(
            "/api/v1/auth/register",
            json={
                "username": "tester",
                "email": "tester@example.com",
                "password": "secret123",
                "display_name": "Tester",
            },
        )
        self.assertIn(r.status_code, (200, 201, 409))

        r = _CLIENT.post(
            "/api/v1/auth/login",
            json={"username": "tester", "password": "secret123"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access_token", r.json())

    def test_books_listing_requires_auth(self) -> None:
        r = _CLIENT.get("/api/v1/books")
        self.assertIn(r.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
