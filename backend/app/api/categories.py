from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.base import get_db
from app.schemas.category import Category as CategorySchema, CategoryCreate
from app.models.book import Category, Book, book_category
from app.models.user import User
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategorySchema])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.get("/{category_id}", response_model=CategorySchema)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.post("", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )

    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()


@router.get("/{category_id}/books")
def get_category_books(
    category_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    query = db.query(Book).join(book_category, Book.id == book_category.c.book_id).filter(
        book_category.c.category_id == category_id
    )
    total = query.count()
    books = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "category": {
            "id": str(category.id),
            "name": category.name
        },
        "books": books,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{category_id}/books/{book_id}")
def add_book_to_category(
    category_id: UUID,
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    if book not in category.books:
        category.books.append(book)
        db.commit()

    return {"message": "Book added to category successfully"}


@router.delete("/{category_id}/books/{book_id}")
def remove_book_from_category(
    category_id: UUID,
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    if book in category.books:
        category.books.remove(book)
        db.commit()

    return {"message": "Book removed from category successfully"}
