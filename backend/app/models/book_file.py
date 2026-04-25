from datetime import datetime
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, PgEnum
from app.models.book import HashStatus


class BookFile(Base):
    __tablename__ = "book_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False, unique=True)
    file_format = Column(String(16), nullable=False)
    file_size = Column(BigInteger)
    file_mtime = Column(DateTime)
    content_hash = Column(String(128), index=True)
    hash_algorithm = Column(String(32))
    hash_status = Column(PgEnum(HashStatus), default=HashStatus.PENDING, nullable=False)
    hash_error = Column(Text)
    is_primary = Column(Boolean, default=True, nullable=False)
    indexed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    book = relationship("Book", back_populates="files")
