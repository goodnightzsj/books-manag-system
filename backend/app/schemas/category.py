from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

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
