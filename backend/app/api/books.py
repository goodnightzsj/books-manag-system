from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.base import get_db
from app.schemas.book import Book as BookSchema, BookCreate, BookUpdate, BookList
from app.models.book import Book
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("", response_model=BookList)
def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Book)
    
    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%")) | 
            (Book.author.ilike(f"%{search}%"))
        )
    
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    
    total = query.count()
    books = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": books,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{book_id}", response_model=BookSchema)
def get_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book

@router.post("", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = Book(**book_data.dict())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.put("/{book_id}", response_model=BookSchema)
def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    update_data = book_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    db.delete(book)
    db.commit()
