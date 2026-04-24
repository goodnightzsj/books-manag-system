from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.base import get_db
from app.models.book import Book, FileFormat
from app.models.user import User
from app.schemas.book import Book as BookSchema, BookCreate, BookList, BookUpdate
from app.services.meilisearch_service import MeiliSearchService
from app.services.search_service import BookSearchService

router = APIRouter(prefix="/books", tags=["Books"])


def _raise_integrity_error(exc: IntegrityError) -> None:
    message = str(getattr(exc, "orig", exc)).lower()
    if "file_path" in message:
        detail = "Book file path already exists"
    elif "isbn" in message:
        detail = "Book ISBN already exists"
    else:
        detail = "Book violates a unique constraint"
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc


@router.get("", response_model=BookList)
def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    author: str | None = None,
    category_id: UUID | None = None,
    file_format: FileFormat | None = Query(None, alias="format"),
    sort: Literal["relevance", "created_at", "updated_at", "title", "rating"] | None = None,
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = BookSearchService(db).search_books(
        q=q,
        author=author,
        category_id=category_id,
        file_format=file_format,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{book_id}", response_model=BookSchema)
def get_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@router.post("", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    search_service = BookSearchService(db)
    book = Book(**book_data.model_dump())
    db.add(book)
    try:
        db.flush()
        search_service.refresh_document(book.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _raise_integrity_error(exc)
    db.refresh(book)
    MeiliSearchService().upsert_book(book)
    return book


@router.put("/{book_id}", response_model=BookSchema)
def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)

    try:
        BookSearchService(db).refresh_document(book.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _raise_integrity_error(exc)
    db.refresh(book)
    MeiliSearchService().upsert_book(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    db.delete(book)
    db.commit()
    MeiliSearchService().delete_book(book_id)
