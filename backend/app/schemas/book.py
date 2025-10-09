from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

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
    file_format: str

class BookUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class Book(BookBase):
    id: UUID
    cover_url: Optional[str]
    file_format: str
    file_size: Optional[int]
    page_count: Optional[int]
    rating: Optional[float]
    rating_count: Optional[int]
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BookList(BaseModel):
    items: List[Book]
    total: int
    page: int
    page_size: int
