from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


ScanJobType = Literal["scan_directory", "scan_file", "rehash", "resync_metadata"]
ScanJobStatus = Literal["queued", "running", "completed", "failed", "partial_success", "cancelled"]
ScanItemStatus = Literal["queued", "processing", "created", "updated", "skipped", "failed"]


class ScanDirectoryRequest(BaseModel):
    directory: str


class ScanFileRequest(BaseModel):
    file_path: str


class ScanJobCreatedResponse(BaseModel):
    job_id: UUID
    status: ScanJobStatus
    message: str


class ScanJobResponse(BaseModel):
    id: UUID
    job_type: ScanJobType
    status: ScanJobStatus
    requested_path: str
    normalized_path: str
    total_items: int
    processed_items: int
    success_items: int
    failed_items: int
    skipped_items: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanJobListResponse(BaseModel):
    items: list[ScanJobResponse]
    total: int


class ScanJobItemResponse(BaseModel):
    id: UUID
    job_id: UUID
    file_path: str
    file_format: Optional[str] = None
    status: ScanItemStatus
    book_id: Optional[UUID] = None
    detected_hash: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanJobItemListResponse(BaseModel):
    items: list[ScanJobItemResponse]
    total: int
