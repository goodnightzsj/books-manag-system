from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.reading import ReadingLocator


class BookNoteCreate(BaseModel):
    locator: ReadingLocator | None = None
    note_text: str


class BookNoteUpdate(BaseModel):
    locator: ReadingLocator | None = None
    note_text: str | None = None


class BookNoteResponse(BaseModel):
    id: UUID
    book_id: UUID
    user_id: UUID
    locator: ReadingLocator | None = None
    note_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookNoteListResponse(BaseModel):
    items: list[BookNoteResponse]
    total: int
