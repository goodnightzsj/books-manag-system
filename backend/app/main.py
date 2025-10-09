from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.db.base import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0"
)

# CORS configuration
# Parse ALLOWED_ORIGINS - support both list and string
allowed_origins = settings.ALLOWED_ORIGINS
if isinstance(allowed_origins, str):
    allowed_origins = [origin.strip() for origin in allowed_origins.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins and allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Books Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
