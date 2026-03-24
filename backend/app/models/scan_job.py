from datetime import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ScanJobType(str, enum.Enum):
    SCAN_DIRECTORY = "scan_directory"
    SCAN_FILE = "scan_file"
    REHASH = "rehash"
    RESYNC_METADATA = "resync_metadata"


class ScanJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"


class ScanItemStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(Enum(ScanJobType), nullable=False)
    status = Column(Enum(ScanJobStatus), nullable=False, default=ScanJobStatus.QUEUED)
    requested_path = Column(Text, nullable=False)
    normalized_path = Column(Text, nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    processed_items = Column(Integer, default=0, nullable=False)
    success_items = Column(Integer, default=0, nullable=False)
    failed_items = Column(Integer, default=0, nullable=False)
    skipped_items = Column(Integer, default=0, nullable=False)
    error_message = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    items = relationship("ScanJobItem", back_populates="job", cascade="all, delete-orphan")


class ScanJobItem(Base):
    __tablename__ = "scan_job_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_format = Column(String, nullable=True)
    status = Column(Enum(ScanItemStatus), nullable=False, default=ScanItemStatus.QUEUED)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    detected_hash = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    job = relationship("ScanJob", back_populates="items")
    book = relationship("Book")
