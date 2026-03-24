from datetime import datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.reading import ReadingStatus


class PdfLocator(BaseModel):
    type: Literal["pdf"]
    page: int = Field(..., ge=1)
    zoom: float | None = Field(default=None, gt=0)


class EpubLocator(BaseModel):
    type: Literal["epub"]
    cfi: str
    chapter: str | None = None
    progression: float | None = Field(default=None, ge=0, le=1)


class TxtLocator(BaseModel):
    type: Literal["txt"]
    line: int = Field(..., ge=1)
    column: int | None = Field(default=None, ge=1)


ReadingLocator = Annotated[Union[PdfLocator, EpubLocator, TxtLocator], Field(discriminator="type")]


class ReadingProgressUpdate(BaseModel):
    current_page: int | None = None
    total_pages: int | None = None
    progress_percent: float | None = Field(default=None, ge=0, le=100)
    status: ReadingStatus | None = None
    locator: ReadingLocator | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ReadingProgressResponse(BaseModel):
    book_id: UUID
    user_id: UUID
    current_page: int | None = None
    total_pages: int | None = None
    progress_percent: float
    status: ReadingStatus
    locator: ReadingLocator | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_read_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class RecentReadingItem(BaseModel):
    book_id: UUID
    title: str
    author: str | None = None
    cover_url: str | None = None
    file_format: str
    progress_percent: float
    status: ReadingStatus
    locator: ReadingLocator | None = None
    last_read_at: datetime | None = None


class RecentReadingList(BaseModel):
    items: list[RecentReadingItem]
    total: int
