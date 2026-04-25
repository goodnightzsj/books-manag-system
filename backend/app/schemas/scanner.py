from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer

from app.models.scan_job import ScanItemStatus, ScanJobStatus, ScanJobType


class ScanDirectoryRequest(BaseModel):
    directory: str


class ScanFileRequest(BaseModel):
    file_path: str


class ScanJobCreatedResponse(BaseModel):
    job_id: UUID
    status: ScanJobStatus
    message: str

    @field_serializer("status")
    def _ser_status(self, v: ScanJobStatus) -> str:
        return v.value if hasattr(v, "value") else v


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
        use_enum_values = True


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
        use_enum_values = True


class ScanJobItemListResponse(BaseModel):
    items: list[ScanJobItemResponse]
    total: int


class ScanJobActionResponse(BaseModel):
    job_id: UUID
    status: ScanJobStatus
    message: str

    @field_serializer("status")
    def _ser_status(self, v: ScanJobStatus) -> str:
        return v.value if hasattr(v, "value") else v


class BookTaskEnqueuedResponse(BaseModel):
    book_id: UUID
    status: Literal["queued"]
    task_id: Optional[str] = None
    message: str
