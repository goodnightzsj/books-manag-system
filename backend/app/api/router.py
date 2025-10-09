from fastapi import APIRouter
from app.api import auth, books, scanner, categories, recommendations, files

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(scanner.router)
api_router.include_router(categories.router)
api_router.include_router(recommendations.router)
api_router.include_router(files.router)
