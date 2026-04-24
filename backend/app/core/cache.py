"""Redis-backed cache wrapper.

Opt-in via ``settings.CACHE_TTL_SECONDS > 0``. Used primarily for the
recommendation routes, where computation is read-heavy and slightly
stale data is acceptable.

Callers use ``cache.get_or_set(key, compute, ttl=?)``; on Redis outage
the compute callback is invoked directly (fail-open).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, url: Optional[str] = None, default_ttl: Optional[int] = None) -> None:
        self.default_ttl = default_ttl if default_ttl is not None else settings.CACHE_TTL_SECONDS
        self._url = url or settings.REDIS_URL
        self._client = None
        if self.default_ttl and self._url:
            try:
                import redis  # lazy

                self._client = redis.Redis.from_url(self._url, decode_responses=True)
            except Exception as exc:  # pragma: no cover
                logger.warning("cache redis init failed: %s", exc)
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None and self.default_ttl > 0

    def get(self, key: str) -> Any:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(key)
        except Exception as exc:  # pragma: no cover
            logger.debug("cache get failed: %s", exc)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.enabled:
            return
        try:
            self._client.set(key, json.dumps(value, default=str), ex=ttl or self.default_ttl)
        except Exception as exc:  # pragma: no cover
            logger.debug("cache set failed: %s", exc)

    def invalidate(self, prefix: str) -> None:
        if not self.enabled:
            return
        try:
            for key in self._client.scan_iter(match=f"{prefix}*", count=200):
                self._client.delete(key)
        except Exception as exc:  # pragma: no cover
            logger.debug("cache invalidate failed: %s", exc)

    def get_or_set(self, key: str, compute: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        if not self.enabled:
            return compute()
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute()
        if value is not None:
            self.set(key, value, ttl=ttl)
        return value


cache = RedisCache()
