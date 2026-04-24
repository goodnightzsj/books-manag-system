from fastapi import APIRouter

from app.api import (
    annotations,
    auth,
    books,
    categories,
    files,
    notes,
    reading_progress,
    recommendations,
    scanner,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(scanner.router)
api_router.include_router(categories.router)
api_router.include_router(recommendations.router)
api_router.include_router(files.router)
api_router.include_router(reading_progress.router)
api_router.include_router(notes.router)
api_router.include_router(annotations.router)
