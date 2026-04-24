"""Behavioral tests for rate limit, cache, and metrics middleware.

Uses a stub `redis` module (registered in sys.modules before the core
modules import it) so the suite does not need a live server. The
framework tests gracefully skip when FastAPI/Starlette is missing.
"""
from __future__ import annotations

import importlib
import os
import sys
import types
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


class _StubRedis:
    """In-memory Redis subset for unit tests."""

    def __init__(self, *_args, **_kwargs) -> None:
        self.store: dict[str, str] = {}
        self.ttl: dict[str, int] = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value if isinstance(value, str) else str(value)
        if ex:
            self.ttl[key] = ex

    def incr(self, key):
        current = int(self.store.get(key, "0")) + 1
        self.store[key] = str(current)
        return current

    def expire(self, key, seconds):
        self.ttl[key] = seconds

    def delete(self, key):
        self.store.pop(key, None)
        self.ttl.pop(key, None)

    def scan_iter(self, match="*", count=100):
        prefix = match.rstrip("*")
        return [k for k in list(self.store.keys()) if k.startswith(prefix)]

    @classmethod
    def from_url(cls, _url, decode_responses=True):  # noqa: ARG003
        return cls()


def _install_fake_redis() -> _StubRedis:
    """Register a stub module so `import redis` yields our implementation."""
    stub_module = types.ModuleType("redis")
    stub_module.Redis = _StubRedis  # type: ignore[attr-defined]
    sys.modules["redis"] = stub_module
    return _StubRedis()


try:
    from fastapi import FastAPI
    from starlette.testclient import TestClient
    _FRAMEWORK_AVAILABLE = True
except Exception:
    _FRAMEWORK_AVAILABLE = False


def _core_modules_importable() -> bool:
    """True only when config.py (and therefore the core middleware) can import."""
    _install_fake_redis()
    try:
        from app.core import cache  # noqa: F401
        from app.core import rate_limit  # noqa: F401
        from app.core import metrics  # noqa: F401
        return True
    except Exception:
        return False


_CORE_AVAILABLE = _core_modules_importable()
_RUNTIME_OK = _FRAMEWORK_AVAILABLE and _CORE_AVAILABLE


@unittest.skipUnless(_RUNTIME_OK, "fastapi/starlette/pydantic_settings not installed")
class RateLimitMiddlewareTests(unittest.TestCase):
    def setUp(self) -> None:
        _install_fake_redis()
        from app.core import rate_limit

        importlib.reload(rate_limit)
        self.rate_limit = rate_limit

    def test_allows_under_limit_and_blocks_over(self) -> None:
        app = FastAPI()
        app.add_middleware(self.rate_limit.RateLimitMiddleware, per_minute=3, redis_url="redis://fake")

        @app.get("/ping")
        def ping():
            return {"ok": True}

        client = TestClient(app)
        for _ in range(3):
            self.assertEqual(client.get("/ping").status_code, 200)
        resp = client.get("/ping")
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp.headers.get("Retry-After"), "60")

    def test_health_endpoint_is_exempt(self) -> None:
        app = FastAPI()
        app.add_middleware(self.rate_limit.RateLimitMiddleware, per_minute=1, redis_url="redis://fake")

        @app.get("/health")
        def health():
            return {"status": "ok"}

        client = TestClient(app)
        for _ in range(5):
            self.assertEqual(client.get("/health").status_code, 200)

    def test_disabled_when_per_minute_is_zero(self) -> None:
        app = FastAPI()
        app.add_middleware(self.rate_limit.RateLimitMiddleware, per_minute=0, redis_url="redis://fake")

        @app.get("/ping")
        def ping():
            return {"ok": True}

        client = TestClient(app)
        for _ in range(10):
            self.assertEqual(client.get("/ping").status_code, 200)


@unittest.skipUnless(_RUNTIME_OK, "fastapi/starlette/pydantic_settings not installed")
class MetricsEndpointTests(unittest.TestCase):
    def test_metrics_counter_line_present(self) -> None:
        from app.core import metrics as metrics_module

        importlib.reload(metrics_module)
        app = FastAPI()
        app.add_middleware(metrics_module.MetricsMiddleware)

        @app.get("/x")
        def x():
            return {"n": 1}

        @app.get("/metrics")
        def metrics_route():
            return metrics_module.metrics_endpoint()

        client = TestClient(app)
        for _ in range(3):
            client.get("/x")
        body = client.get("/metrics").text
        self.assertIn("books_http_requests_total", body)


@unittest.skipUnless(_CORE_AVAILABLE, "pydantic_settings not installed (config.py cannot import)")
class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        _install_fake_redis()
        from app.core import cache as cache_module

        importlib.reload(cache_module)
        self.cache_module = cache_module

    def test_cache_get_or_set_computes_once_when_enabled(self) -> None:
        c = self.cache_module.RedisCache(url="redis://fake", default_ttl=30)
        self.assertTrue(c.enabled)
        calls = {"n": 0}

        def compute():
            calls["n"] += 1
            return {"v": 42}

        first = c.get_or_set("k", compute)
        second = c.get_or_set("k", compute)
        self.assertEqual(first, second)
        self.assertEqual(calls["n"], 1)

    def test_cache_invalidate_removes_by_prefix(self) -> None:
        c = self.cache_module.RedisCache(url="redis://fake", default_ttl=30)
        c.set("reco:abc", {"x": 1})
        c.set("reco:def", {"x": 2})
        c.set("other:ghi", {"x": 3})
        c.invalidate("reco:")
        self.assertIsNone(c.get("reco:abc"))
        self.assertIsNone(c.get("reco:def"))
        self.assertEqual(c.get("other:ghi"), {"x": 3})

    def test_cache_disabled_when_ttl_zero(self) -> None:
        c = self.cache_module.RedisCache(default_ttl=0)
        calls = {"n": 0}

        def compute():
            calls["n"] += 1
            return "v"

        self.assertEqual(c.get_or_set("k", compute), "v")
        self.assertEqual(c.get_or_set("k", compute), "v")
        self.assertEqual(calls["n"], 2)
        self.assertFalse(c.enabled)


if __name__ == "__main__":
    unittest.main()
