from uuid import UUID

from app.celery_app import celery_app
from app.core.config import settings


class TaskDispatchService:
    def enqueue_scan_directory(self, job_id: UUID) -> str:
        result = celery_app.send_task("scan.run_directory_job", args=[str(job_id)], queue=settings.BOOKS_SCAN_QUEUE)
        return result.id

    def enqueue_scan_file(self, job_id: UUID) -> str:
        result = celery_app.send_task("scan.run_file_job", args=[str(job_id)], queue=settings.BOOKS_SCAN_QUEUE)
        return result.id

    def enqueue_process_scan_item(self, item_id: UUID) -> str:
        result = celery_app.send_task("scan.process_scan_item", args=[str(item_id)], queue=settings.BOOKS_SCAN_QUEUE)
        return result.id

    def enqueue_retry_failed_items(self, job_id: UUID) -> str:
        result = celery_app.send_task("scan.retry_failed_items", args=[str(job_id)], queue=settings.BOOKS_SCAN_QUEUE)
        return result.id

    def enqueue_compute_hash(self, book_id: UUID, item_id: UUID | None = None) -> str:
        args = [str(book_id)]
        if item_id is not None:
            args.append(str(item_id))
        result = celery_app.send_task("hash.compute_book_hash", args=args, queue=settings.BOOKS_SCAN_QUEUE)
        return result.id

    def enqueue_metadata_sync(self, book_id: UUID, *, force: bool = False) -> str:
        result = celery_app.send_task(
            "metadata.sync_book_metadata",
            args=[str(book_id)],
            kwargs={"force": force},
            queue=settings.BOOKS_ENRICH_QUEUE,
        )
        return result.id

    def enqueue_cover_sync(
        self,
        book_id: UUID,
        *,
        prefer_remote: bool = False,
        source_url: str | None = None,
        force: bool = False,
    ) -> str:
        result = celery_app.send_task(
            "cover.extract_or_download_cover",
            args=[str(book_id)],
            kwargs={
                "prefer_remote": prefer_remote,
                "source_url": source_url,
                "force": force,
            },
            queue=settings.BOOKS_ENRICH_QUEUE,
        )
        return result.id

    def enqueue_reconcile_stalled_jobs(self) -> str:
        result = celery_app.send_task(
            "maintenance.reconcile_stalled_jobs",
            queue=settings.BOOKS_MAINTENANCE_QUEUE,
        )
        return result.id
