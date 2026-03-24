from datetime import datetime, timedelta

from app.celery_app import celery_app
from app.core.config import settings
from app.db.base import SessionLocal
from app.models.scan_job import ScanItemStatus, ScanJob, ScanJobItem, ScanJobStatus
from app.services.scan_job_service import ScanJobService


@celery_app.task(name="maintenance.reconcile_stalled_jobs")
def reconcile_stalled_jobs():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        item_cutoff = now - timedelta(seconds=settings.SCAN_ITEM_STALLED_SECONDS)
        job_cutoff = now - timedelta(seconds=settings.SCAN_JOB_STALLED_SECONDS)
        scan_jobs = ScanJobService(db)

        stale_items = (
            db.query(ScanJobItem)
            .filter(
                ScanJobItem.status == ScanItemStatus.PROCESSING,
                ScanJobItem.updated_at < item_cutoff,
            )
            .all()
        )
        affected_job_ids: set = set()
        for item in stale_items:
            scan_jobs.mark_item_finished(
                item.id,
                status="failed",
                book_id=item.book_id,
                detected_hash=item.detected_hash,
                error_message="maintenance: processing timeout",
            )
            affected_job_ids.add(item.job_id)

        stale_empty_jobs = (
            db.query(ScanJob)
            .filter(
                ScanJob.status == ScanJobStatus.RUNNING,
                ScanJob.started_at.isnot(None),
                ScanJob.started_at < job_cutoff,
                ScanJob.total_items == 0,
            )
            .all()
        )
        for job in stale_empty_jobs:
            job.status = ScanJobStatus.FAILED
            job.error_message = job.error_message or "maintenance: job timed out before producing items"
            job.finished_at = now
        if stale_empty_jobs:
            db.commit()

        finalized_jobs: dict[str, str] = {}
        running_complete_jobs = (
            db.query(ScanJob)
            .filter(
                ScanJob.status == ScanJobStatus.RUNNING,
                ScanJob.total_items > 0,
                ScanJob.processed_items >= ScanJob.total_items,
            )
            .all()
        )
        for job in running_complete_jobs:
            affected_job_ids.add(job.id)

        for job_id in affected_job_ids:
            finalized_jobs[str(job_id)] = scan_jobs.maybe_finalize_job(job_id)

        return {
            "stale_items_failed": len(stale_items),
            "stale_empty_jobs_failed": len(stale_empty_jobs),
            "jobs_reconciled": len(finalized_jobs),
            "job_statuses": finalized_jobs,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
