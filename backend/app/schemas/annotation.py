from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.reading import ReadingLocator


class BookmarkCreate(BaseModel):
    locator: ReadingLocator
    title: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = None


class BookmarkUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = None
    locator: Optional[ReadingLocator] = None


class BookmarkResponse(BaseModel):
    id: UUID
    book_id: UUID
    locator: ReadingLocator
    title: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    items: list[BookmarkResponse]
    total: int


class AnnotationCreate(BaseModel):
    locator_start: ReadingLocator
    locator_end: Optional[ReadingLocator] = None
    highlight_text: Optional[str] = None
    note: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=32)


class AnnotationUpdate(BaseModel):
    locator_start: Optional[ReadingLocator] = None
    locator_end: Optional[ReadingLocator] = None
    highlight_text: Optional[str] = None
    note: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=32)


class AnnotationResponse(BaseModel):
    id: UUID
    book_id: UUID
    locator_start: ReadingLocator
    locator_end: Optional[ReadingLocator] = None
    highlight_text: Optional[str] = None
    note: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    items: list[AnnotationResponse]
    total: int
