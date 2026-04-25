from sqlalchemy import Column, String, DateTime, Float, Integer, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base, PgEnum


class ReadingStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    READING = "reading"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_reading_progress_user_book"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey('books.id'), nullable=False)
    current_page = Column(Integer)
    total_pages = Column(Integer)
    progress_percent = Column(Float, default=0.0)
    status = Column(PgEnum(ReadingStatus), default=ReadingStatus.NOT_STARTED, nullable=False)
    locator = Column(JSONB)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    last_read_at = Column(DateTime)
    notes = Column(Text)
    bookmarks = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book", back_populates="reading_progress")
