"""Redis-backed token-bucket rate limiter, mounted as FastAPI middleware.

Enabled when ``settings.RATE_LIMIT_PER_MINUTE > 0``. Keys are derived
from the client IP (``X-Forwarded-For`` first, else ``request.client``)
so a reverse proxy must pass the forwarded header. Authenticated
requests get a separate bucket keyed by user id when a bearer token is
present -- prevents one noisy IP from throttling all users behind NAT.

Fail-open: if Redis is unreachable the middleware lets the request
through; this is a conscious trade-off -- rate limiting is a safety
net, not a correctness boundary, and an outage should not 503 the API.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        per_minute: int,
        redis_url: Optional[str] = None,
    ) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self.window = 60
        self._redis = None
        if per_minute > 0 and redis_url:
            try:
                import redis  # lazy import so tests don't require the library

                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
            except Exception as exc:  # pragma: no cover
                logger.warning("rate-limit redis init failed: %s", exc)
                self._redis = None

    async def dispatch(self, request: Request, call_next):
        if self.per_minute <= 0 or self._redis is None:
            return await call_next(request)
        # Exempt health / metrics endpoints so probes never get throttled.
        if request.url.path in {"/health", "/metrics", "/"}:
            return await call_next(request)

        key = self._bucket_key(request)
        try:
            count = self._redis.incr(key)
            if count == 1:
                self._redis.expire(key, self.window)
        except Exception as exc:  # pragma: no cover
            logger.debug("rate-limit redis op failed, fail-open: %s", exc)
            return await call_next(request)

        if int(count) > self.per_minute:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(self.window)},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.per_minute - int(count)))
        return response

    def _bucket_key(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
            if token:
                return f"rl:tok:{token[-16:]}:{int(time.time() // self.window)}"
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip and request.client is not None:
            ip = request.client.host
        return f"rl:ip:{ip or 'unknown'}:{int(time.time() // self.window)}"
