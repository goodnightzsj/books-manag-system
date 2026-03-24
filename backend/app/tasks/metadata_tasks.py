import logging
from uuid import UUID

from app.celery_app import celery_app
from app.core.config import settings
from app.db.base import SessionLocal
from app.services.metadata_service import MetadataSyncService
from app.services.task_dispatch_service import TaskDispatchService

logger = logging.getLogger(__name__)


@celery_app.task(name="metadata.sync_book_metadata")
def sync_book_metadata(book_id: str, force: bool = False):
    db = SessionLocal()
    try:
        book_uuid = UUID(book_id)
        result = MetadataSyncService(
            db,
            google_api_key=settings.GOOGLE_BOOKS_API_KEY,
        ).sync_book(book_uuid, force=force)
        if result is None:
            return None

        db.commit()

        if result.found:
            try:
                TaskDispatchService().enqueue_cover_sync(
                    book_uuid,
                    prefer_remote=bool(result.cover_source_url),
                    source_url=result.cover_source_url,
                    force=force,
                )
            except Exception as exc:
                logger.error("Error queueing cover sync for %s: %s", book_id, exc)

        return {
            "book_id": str(result.book_id),
            "provider": result.provider,
            "updated_fields": result.updated_fields,
            "found": result.found,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
