from sqlalchemy import Column, String, DateTime, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base

class ReadingStatus(str, enum.Enum):
    READING = "reading"
    COMPLETED = "completed"
    PLAN_TO_READ = "plan_to_read"

class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey('books.id'), nullable=False)
    progress = Column(Float, default=0.0)  # 0-100
    current_location = Column(String)  # page number or chapter
    last_read_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Enum(ReadingStatus), default=ReadingStatus.READING, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book", back_populates="reading_progress")
