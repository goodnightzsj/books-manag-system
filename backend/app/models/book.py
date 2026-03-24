from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Enum, JSON, BigInteger, ForeignKey, Table
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base

class FileFormat(str, enum.Enum):
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    AZW3 = "azw3"
    TXT = "txt"
    DJVU = "djvu"


class HashStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"

# Association table for many-to-many relationship
book_category = Table(
    'book_categories',
    Base.metadata,
    Column('book_id', UUID(as_uuid=True), ForeignKey('books.id'), primary_key=True),
    Column('category_id', UUID(as_uuid=True), ForeignKey('categories.id'), primary_key=True)
)

class Book(Base):
    __tablename__ = "books"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    subtitle = Column(String)
    author = Column(String, index=True)
    publisher = Column(String)
    publish_date = Column(DateTime)
    isbn = Column(String, unique=True, index=True)
    description = Column(Text)
    cover_url = Column(String)
    file_path = Column(String, nullable=False)
    file_format = Column(Enum(FileFormat), nullable=False)
    file_size = Column(BigInteger)
    file_mtime = Column(DateTime)
    content_hash = Column(String, index=True)
    hash_algorithm = Column(String)
    hash_status = Column(Enum(HashStatus), default=HashStatus.PENDING, nullable=False)
    hash_error = Column(Text)
    language = Column(String, default="zh")
    page_count = Column(Integer)
    rating = Column(Float)
    rating_count = Column(Integer)
    tags = Column(JSON, default=list)
    book_metadata = Column(JSON, default=dict)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    source_provider = Column(String)
    metadata_synced_at = Column(DateTime)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    indexed_at = Column(DateTime)
    
    # Relationships
    categories = relationship("Category", secondary=book_category, back_populates="books")
    reading_progress = relationship("ReadingProgress", back_populates="book", cascade="all, delete-orphan")
    notes = relationship("BookNote", back_populates="book", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    books = relationship("Book", secondary=book_category, back_populates="categories")
    parent = relationship("Category", back_populates="children", remote_side=[id])
    children = relationship("Category", back_populates="parent")
