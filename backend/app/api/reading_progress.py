from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.reading import RecentReadingList, ReadingProgressResponse, ReadingProgressUpdate
from app.services.reading_service import ReadingProgressService

router = APIRouter(prefix="/reading-progress", tags=["ReadingProgress"])


@router.get("/recent", response_model=RecentReadingList)
def get_recent_reading(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = ReadingProgressService(db).list_recent_for_user(user=current_user, limit=limit)
    return {
        "items": [
            {
                "book_id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_url": book.cover_url,
                "file_format": book.file_format.value,
                "progress_percent": progress.progress_percent,
                "status": progress.status,
                "locator": progress.locator,
                "last_read_at": progress.last_read_at,
            }
            for progress, book in items
        ],
        "total": total,
    }


@router.get("/{book_id}", response_model=ReadingProgressResponse)
def get_reading_progress(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    progress = ReadingProgressService(db).get_for_user(book_id=book_id, user=current_user)
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading progress not found")
    return progress


@router.put("/{book_id}", response_model=ReadingProgressResponse)
def upsert_reading_progress(
    book_id: UUID,
    progress_data: ReadingProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ReadingProgressService(db).upsert_for_user(
            book_id=book_id,
            user=current_user,
            payload=progress_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
