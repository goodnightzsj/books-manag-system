"""Prometheus metrics: a middleware + /metrics endpoint.

Uses ``prometheus_client`` when available; otherwise falls back to a
minimal in-process counter so tests and environments without the lib
still boot. Cardinality is kept low by recording route templates, not
raw URL paths.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

logger = logging.getLogger(__name__)

try:  # pragma: no cover
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )

    _HTTP_REQUESTS = Counter(
        "books_http_requests_total",
        "Total HTTP requests",
        ["method", "route", "status"],
    )
    _HTTP_LATENCY = Histogram(
        "books_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "route"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    _PROM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROM_AVAILABLE = False
    _HTTP_REQUESTS = None
    _HTTP_LATENCY = None
    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"

    _COUNTERS: dict[tuple[str, str, str], int] = {}

    def generate_latest() -> bytes:  # type: ignore[misc]
        lines = ["# fallback metrics (prometheus_client not installed)"]
        for (method, route, status), count in _COUNTERS.items():
            lines.append(
                f'books_http_requests_total{{method="{method}",route="{route}",status="{status}"}} {count}'
            )
        return ("\n".join(lines) + "\n").encode()


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path  # type: ignore[no-any-return]
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Any:
        start = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - start
            _record(request.method, _route_template(request), "500", elapsed)
            raise
        elapsed = time.perf_counter() - start
        _record(request.method, _route_template(request), str(response.status_code), elapsed)
        return response


def _record(method: str, route: str, status: str, elapsed: float) -> None:
    if _PROM_AVAILABLE:
        _HTTP_REQUESTS.labels(method, route, status).inc()
        _HTTP_LATENCY.labels(method, route).observe(elapsed)
    else:
        key = (method, route, status)
        _COUNTERS[key] = _COUNTERS.get(key, 0) + 1


def metrics_endpoint() -> PlainTextResponse:
    payload = generate_latest()
    return PlainTextResponse(payload, media_type=CONTENT_TYPE_LATEST)
