from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_endpoint
from app.core.rate_limit import RateLimitMiddleware

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
)

# CORS configuration
allowed_origins = settings.ALLOWED_ORIGINS
if isinstance(allowed_origins, str):
    allowed_origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins and allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)

if settings.RATE_LIMIT_PER_MINUTE > 0:
    app.add_middleware(
        RateLimitMiddleware,
        per_minute=settings.RATE_LIMIT_PER_MINUTE,
        redis_url=settings.REDIS_URL,
    )

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "message": "Books Management System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if settings.METRICS_ENABLED:

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return metrics_endpoint()
