from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.base import get_db
from app.models.book import Book
from app.models.user import User
from app.schemas.scanner import (
    ScanDirectoryRequest,
    ScanFileRequest,
    ScanJobCreatedResponse,
    ScanJobItemListResponse,
    ScanJobListResponse,
    ScanJobResponse,
)
from app.services.file_access_service import FileAccessService
from app.services.scan_job_service import ScanJobService
from app.services.task_dispatch_service import TaskDispatchService

router = APIRouter(prefix="/scanner", tags=["Scanner"])


@router.post("/jobs/directory", response_model=ScanJobCreatedResponse)
def create_directory_scan_job(
    request: ScanDirectoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        file_access = FileAccessService()
        normalized = file_access.resolve_scan_root(request.directory)
        if not Path(normalized).is_dir():
            raise ValueError(f"Not a directory: {normalized}")
        job = ScanJobService(db).create_job(
            job_type="scan_directory",
            requested_path=request.directory,
            normalized_path=normalized,
            created_by=current_user.id,
        )
        TaskDispatchService().enqueue_scan_directory(job.id)
        return ScanJobCreatedResponse(job_id=job.id, status="queued", message="Directory scan queued")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/jobs/file", response_model=ScanJobCreatedResponse)
def create_file_scan_job(
    request: ScanFileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        normalized = FileAccessService().ensure_supported_file(request.file_path)
        job = ScanJobService(db).create_job(
            job_type="scan_file",
            requested_path=request.file_path,
            normalized_path=normalized,
            created_by=current_user.id,
        )
        TaskDispatchService().enqueue_scan_file(job.id)
        return ScanJobCreatedResponse(job_id=job.id, status="queued", message="File scan queued")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/jobs", response_model=ScanJobListResponse)
def list_scan_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    items, total = ScanJobService(db).list_jobs(limit=limit)
    return ScanJobListResponse(items=items, total=total)


@router.get("/jobs/{job_id}", response_model=ScanJobResponse)
def get_scan_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    job = ScanJobService(db).get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    return job


@router.get("/jobs/{job_id}/items", response_model=ScanJobItemListResponse)
def get_scan_job_items(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ScanJobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    items, total = service.get_job_items(job_id)
    return ScanJobItemListResponse(items=items, total=total)


@router.post("/jobs/{job_id}/retry-failed")
def retry_failed_scan_items(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ScanJobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    TaskDispatchService().enqueue_retry_failed_items(job_id)
    return {"job_id": str(job_id), "status": "queued", "message": "Retry failed items queued"}


@router.post("/books/{book_id}/metadata-sync")
def queue_metadata_sync(
    book_id: UUID,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    task_id = TaskDispatchService().enqueue_metadata_sync(book_id, force=force)
    return {
        "book_id": str(book_id),
        "status": "queued",
        "task_id": task_id,
        "message": "Metadata sync queued",
    }


@router.post("/books/{book_id}/extract-cover")
def queue_cover_extract(
    book_id: UUID,
    prefer_remote: bool = Query(False),
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    metadata_cover_url = None
    if isinstance(book.book_metadata, dict):
        cover_candidate = book.book_metadata.get("cover_url")
        if isinstance(cover_candidate, str) and cover_candidate.strip():
            metadata_cover_url = cover_candidate.strip()

    task_id = TaskDispatchService().enqueue_cover_sync(
        book_id,
        prefer_remote=prefer_remote,
        source_url=metadata_cover_url,
        force=force,
    )
    return {
        "book_id": str(book_id),
        "status": "queued",
        "task_id": task_id,
        "message": "Cover extraction queued",
    }
