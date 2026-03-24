from uuid import UUID

from app.celery_app import celery_app
from app.core.config import settings
from app.db.base import SessionLocal
from app.models.book import Book
from app.services.cover_service import CoverService


@celery_app.task(name="cover.extract_or_download_cover")
def extract_or_download_cover(
    book_id: str,
    prefer_remote: bool = False,
    source_url: str | None = None,
    force: bool = False,
):
    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == UUID(book_id)).first()
        if not book:
            return None

        cover_url = CoverService(settings.UPLOADS_DIR).ensure_cover(
            book,
            prefer_remote=prefer_remote,
            source_url=source_url,
            force=force,
        )
        if not cover_url:
            return {"book_id": book_id, "status": "not_found", "cover_url": None}

        if book.cover_url != cover_url:
            book.cover_url = cover_url
            db.commit()
        else:
            db.rollback()

        return {"book_id": book_id, "status": "ok", "cover_url": cover_url}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
