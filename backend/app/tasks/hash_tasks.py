from uuid import UUID

from app.db.base import SessionLocal
from app.models.book import Book, HashStatus
from app.services.book_ingest_service import BookIngestService
from app.services.file_access_service import FileAccessService
from app.services.hash_service import HashService
from app.celery_app import celery_app


@celery_app.task(name="hash.compute_book_hash")
def compute_book_hash(book_id: str, item_id: str | None = None):
    db = SessionLocal()
    try:
        book_uuid = UUID(book_id)
        item_uuid = UUID(item_id) if item_id else None
        book = db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            return None

        file_path = FileAccessService().resolve_book_file(book.file_path)
        hash_service = HashService()
        content_hash = hash_service.compute_sha256(file_path)
        resolved_book = BookIngestService(db).apply_hash_result(
            book_id=book_uuid,
            content_hash=content_hash,
            algorithm=hash_service.DEFAULT_ALGORITHM,
            item_id=item_uuid,
        )
        db.commit()
        return str(resolved_book.id)
    except Exception as exc:
        error_message = HashService().classify_error(exc)
        book = db.query(Book).filter(Book.id == UUID(book_id)).first()
        if book:
            book.hash_status = HashStatus.FAILED
            book.hash_error = error_message
            db.commit()
        else:
            db.rollback()
        raise
    finally:
        db.close()
