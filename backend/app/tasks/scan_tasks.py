from uuid import UUID

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.models.book import Book, HashStatus
from app.services.book_ingest_service import BookIngestService
from app.services.file_access_service import FileAccessService
from app.services.metadata_service import MetadataExtractor
from app.services.scan_job_service import ScanJobService
from app.services.scanner_service import ScanService
from app.services.task_dispatch_service import TaskDispatchService


@celery_app.task(name="scan.run_directory_job")
def run_directory_job(job_id: str):
    db = SessionLocal()
    try:
        file_access = FileAccessService()
        scan_jobs = ScanJobService(db)
        dispatch = TaskDispatchService()
        job = scan_jobs.claim_job(UUID(job_id))
        if not job:
            return None
        files = list(file_access.iter_supported_files(job.normalized_path))
        items = scan_jobs.add_items(job.id, files)
        for item in items:
            dispatch.enqueue_process_scan_item(item.id)
        if not items:
            scan_jobs.maybe_finalize_job(job.id)
        return str(job.id)
    except Exception as exc:
        ScanJobService(db).mark_job_failed(UUID(job_id), str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="scan.run_file_job")
def run_file_job(job_id: str):
    db = SessionLocal()
    try:
        scan_jobs = ScanJobService(db)
        dispatch = TaskDispatchService()
        job = scan_jobs.claim_job(UUID(job_id))
        if not job:
            return None
        files = list(FileAccessService().iter_supported_files(job.normalized_path))
        items = scan_jobs.add_items(job.id, files)
        for item in items:
            dispatch.enqueue_process_scan_item(item.id)
        if not items:
            scan_jobs.maybe_finalize_job(job.id)
        return str(job.id)
    except Exception as exc:
        ScanJobService(db).mark_job_failed(UUID(job_id), str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="scan.process_scan_item")
def process_scan_item(item_id: str):
    db = SessionLocal()
    item_uuid = UUID(item_id)
    job_id = None
    try:
        scan_jobs = ScanJobService(db)
        item = scan_jobs.claim_item(item_uuid)
        if not item:
            return None
        job_id = item.job_id
        scan_service = ScanService(db, FileAccessService(), MetadataExtractor(), BookIngestService(db))
        result = scan_service.process_file(item.file_path)
        scan_jobs.mark_item_finished(item_uuid, status=result.action, book_id=result.book_id)
        scan_jobs.maybe_finalize_job(job_id)
        if result.should_hash:
            try:
                TaskDispatchService().enqueue_compute_hash(result.book_id, item_uuid)
            except Exception as exc:
                book = db.query(Book).filter(Book.id == result.book_id).first()
                if book:
                    book.hash_status = HashStatus.FAILED
                    book.hash_error = f"dispatch_error: {exc}"
                    db.commit()
        return str(result.book_id)
    except Exception as exc:
        scan_jobs = ScanJobService(db)
        scan_jobs.mark_item_finished(item_uuid, status="failed", error_message=str(exc))
        if job_id is not None:
            scan_jobs.maybe_finalize_job(job_id)
        raise
    finally:
        db.close()


@celery_app.task(name="scan.retry_failed_items")
def retry_failed_items(job_id: str):
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        scan_jobs = ScanJobService(db)
        dispatch = TaskDispatchService()
        retried = scan_jobs.retry_failed_items(job_uuid)
        items, _ = scan_jobs.get_job_items(job_uuid)
        for item in items:
            if item.status.value == "queued":
                dispatch.enqueue_process_scan_item(item.id)
        return retried
    finally:
        db.close()
