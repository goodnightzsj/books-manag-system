from datetime import datetime
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.scan_job import ScanItemStatus, ScanJob, ScanJobItem, ScanJobStatus, ScanJobType
from app.services.file_access_service import DiscoveredFile


class ScanJobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, *, job_type: str, requested_path: str, normalized_path: str, created_by: UUID | None) -> ScanJob:
        job = ScanJob(
            job_type=ScanJobType(job_type),
            status=ScanJobStatus.QUEUED,
            requested_path=requested_path,
            normalized_path=normalized_path,
            created_by=created_by,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(self, *, limit: int = 20) -> tuple[list[ScanJob], int]:
        query = self.db.query(ScanJob).order_by(ScanJob.created_at.desc())
        return query.limit(limit).all(), query.count()

    def get_job(self, job_id: UUID) -> ScanJob | None:
        return self.db.query(ScanJob).filter(ScanJob.id == job_id).first()

    def get_job_items(self, job_id: UUID) -> tuple[list[ScanJobItem], int]:
        query = self.db.query(ScanJobItem).filter(ScanJobItem.job_id == job_id).order_by(ScanJobItem.created_at.asc())
        return query.all(), query.count()

    def claim_job(self, job_id: UUID) -> ScanJob | None:
        # Row lock so two workers can't both flip the same QUEUED job to RUNNING.
        job = (
            self.db.query(ScanJob)
            .filter(ScanJob.id == job_id)
            .with_for_update()
            .first()
        )
        if not job or job.status != ScanJobStatus.QUEUED:
            self.db.commit()
            return None
        job.status = ScanJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def add_items(self, job_id: UUID, files: Iterable[DiscoveredFile]) -> list[ScanJobItem]:
        items: list[ScanJobItem] = []
        for discovered in files:
            item = ScanJobItem(
                job_id=job_id,
                file_path=discovered.path,
                file_format=discovered.file_format,
                status=ScanItemStatus.QUEUED,
            )
            self.db.add(item)
            items.append(item)
        self.db.flush()
        job = self.get_job(job_id)
        if job:
            job.total_items = len(items)
        self.db.commit()
        return items

    def claim_item(self, item_id: UUID) -> ScanJobItem | None:
        item = (
            self.db.query(ScanJobItem)
            .filter(ScanJobItem.id == item_id)
            .with_for_update()
            .first()
        )
        if not item or item.status not in {ScanItemStatus.QUEUED, ScanItemStatus.FAILED}:
            self.db.commit()
            return None
        item.status = ScanItemStatus.PROCESSING
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_item_finished(self, item_id: UUID, *, status: str, book_id: UUID | None = None, detected_hash: str | None = None, error_message: str | None = None) -> None:
        item_status = ScanItemStatus(status)
        # Transition the item only if it is still in-flight. The rowcount tells
        # us whether *this* call actually moved it, which keeps the per-job
        # counter bump idempotent under retries / duplicate task delivery.
        moved = (
            self.db.query(ScanJobItem)
            .filter(
                ScanJobItem.id == item_id,
                ScanJobItem.status.in_({ScanItemStatus.QUEUED, ScanItemStatus.PROCESSING}),
            )
            .update(
                {
                    ScanJobItem.status: item_status,
                    ScanJobItem.book_id: book_id,
                    ScanJobItem.detected_hash: detected_hash,
                    ScanJobItem.error_message: error_message,
                    ScanJobItem.updated_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        if not moved:
            self.db.commit()
            return

        job_id = self.db.query(ScanJobItem.job_id).filter(ScanJobItem.id == item_id).scalar()
        if job_id is not None:
            increments = {ScanJob.processed_items: ScanJob.processed_items + 1}
            if item_status in {ScanItemStatus.CREATED, ScanItemStatus.UPDATED}:
                increments[ScanJob.success_items] = ScanJob.success_items + 1
            elif item_status == ScanItemStatus.SKIPPED:
                increments[ScanJob.skipped_items] = ScanJob.skipped_items + 1
            elif item_status == ScanItemStatus.FAILED:
                increments[ScanJob.failed_items] = ScanJob.failed_items + 1
            # In-DB UPDATE => atomic increment, no read-modify-write race.
            self.db.query(ScanJob).filter(ScanJob.id == job_id).update(
                increments, synchronize_session=False
            )
        self.db.commit()

    def maybe_finalize_job(self, job_id: UUID) -> str:
        # Lock the job row: only one worker gets to perform the finalize
        # transition even when several items finish at the same moment.
        job = (
            self.db.query(ScanJob)
            .filter(ScanJob.id == job_id)
            .with_for_update()
            .first()
        )
        if not job:
            self.db.commit()
            return "running"
        if job.status in {
            ScanJobStatus.COMPLETED,
            ScanJobStatus.PARTIAL_SUCCESS,
            ScanJobStatus.FAILED,
        }:
            self.db.commit()
            return job.status.value
        if job.total_items == 0:
            job.status = ScanJobStatus.COMPLETED
            job.finished_at = datetime.utcnow()
            self.db.commit()
            return job.status.value
        if job.processed_items < job.total_items:
            self.db.commit()
            return "running"
        if job.failed_items and job.success_items:
            job.status = ScanJobStatus.PARTIAL_SUCCESS
        elif job.failed_items == job.total_items:
            job.status = ScanJobStatus.FAILED
        else:
            job.status = ScanJobStatus.COMPLETED
        job.finished_at = datetime.utcnow()
        self.db.commit()
        return job.status.value

    def mark_job_failed(self, job_id: UUID, error_message: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return
        job.status = ScanJobStatus.FAILED
        job.error_message = error_message
        job.finished_at = datetime.utcnow()
        self.db.commit()

    def retry_failed_items(self, job_id: UUID) -> int:
        items = self.db.query(ScanJobItem).filter(ScanJobItem.job_id == job_id, ScanJobItem.status == ScanItemStatus.FAILED).all()
        if not items:
            return 0

        for item in items:
            item.status = ScanItemStatus.QUEUED
            item.error_message = None
            item.updated_at = datetime.utcnow()
        job = self.get_job(job_id)
        if job:
            job.status = ScanJobStatus.RUNNING
            job.failed_items = max(0, job.failed_items - len(items))
            job.processed_items = max(0, job.processed_items - len(items))
            job.finished_at = None
            job.error_message = None
        self.db.commit()
        return len(items)
