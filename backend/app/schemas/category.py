from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.schemas.book import Book as BookSchema

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryRef(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class CategoryBooksResponse(BaseModel):
    """Paginated books inside a category.

    Books are projected through ``BookSchema`` (not the ORM object) so the
    response never leaks internal columns (``file_path`` etc.) and never
    triggers lazy-loads of per-user relationships.
    """
    category: CategoryRef
    books: List[BookSchema]
    total: int
    page: int
    page_size: int
