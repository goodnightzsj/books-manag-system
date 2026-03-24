from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.reading import ReadingProgress, ReadingStatus
from app.models.user import User


class ReadingProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, *, book_id: UUID, user: User) -> ReadingProgress | None:
        return (
            self.db.query(ReadingProgress)
            .filter(ReadingProgress.book_id == book_id, ReadingProgress.user_id == user.id)
            .first()
        )

    def upsert_for_user(self, *, book_id: UUID, user: User, payload: dict) -> ReadingProgress:
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError("Book not found")

        progress = self.get_for_user(book_id=book_id, user=user)
        if progress is None:
            progress = ReadingProgress(book_id=book_id, user_id=user.id)
            self.db.add(progress)

        for field in [
            "current_page",
            "total_pages",
            "progress_percent",
            "status",
            "locator",
            "started_at",
            "finished_at",
        ]:
            if field in payload:
                setattr(progress, field, payload[field])

        if progress.progress_percent is None:
            progress.progress_percent = 0.0

        if progress.progress_percent >= 100:
            progress.progress_percent = 100.0
            progress.status = ReadingStatus.COMPLETED
            progress.finished_at = progress.finished_at or datetime.utcnow()
        elif progress.progress_percent > 0 and progress.status == ReadingStatus.NOT_STARTED:
            progress.status = ReadingStatus.READING

        if progress.status == ReadingStatus.READING and progress.started_at is None:
            progress.started_at = datetime.utcnow()

        progress.last_read_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def list_recent_for_user(self, *, user: User, limit: int) -> tuple[list[tuple[ReadingProgress, Book]], int]:
        query = (
            self.db.query(ReadingProgress, Book)
            .join(Book, Book.id == ReadingProgress.book_id)
            .filter(ReadingProgress.user_id == user.id)
            .order_by(ReadingProgress.last_read_at.desc().nullslast(), ReadingProgress.updated_at.desc())
        )
        total = query.count()
        items = query.limit(limit).all()
        return items, total
