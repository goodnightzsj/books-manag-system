from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.book import FileFormat, HashStatus


class BookBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    language: str = "zh"


class BookCreate(BookBase):
    file_path: str
    file_format: FileFormat


class BookUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class Book(BookBase):
    id: UUID
    cover_url: Optional[str] = None
    file_format: FileFormat
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    hash_status: HashStatus
    metadata_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookList(BaseModel):
    items: List[Book]
    total: int
    page: int
    page_size: int
