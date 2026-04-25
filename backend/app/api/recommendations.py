from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from uuid import UUID

from app.db.base import get_db
from app.schemas.book import Book as BookSchema
from app.models.book import Book, Category, book_category
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/random", response_model=List[BookSchema])
def get_random_recommendations(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    books = db.query(Book) \
        .filter(Book.rating.isnot(None)) \
        .order_by(Book.rating.desc()) \
        .limit(count * 2) \
        .all()

    if not books:
        books = db.query(Book).order_by(func.random()).limit(count).all()
    else:
        import random
        books = random.sample(books, min(count, len(books)))

    return books


@router.get("/category/{category_id}", response_model=List[BookSchema])
def get_category_recommendations(
    category_id: UUID,
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    books = db.query(Book).join(book_category, Book.id == book_category.c.book_id).filter(
        book_category.c.category_id == category_id,
        Book.rating.isnot(None)
    ).order_by(Book.rating.desc()).limit(count).all()
    return books


@router.get("/trending", response_model=List[BookSchema])
def get_trending_books(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    books = db.query(Book) \
        .filter(Book.rating.isnot(None)) \
        .filter(Book.rating_count.isnot(None)) \
        .order_by(Book.rating.desc(), Book.rating_count.desc()) \
        .limit(count) \
        .all()

    return books


@router.get("/personalized", response_model=List[BookSchema])
def get_personalized_recommendations(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.reading import ReadingProgress, ReadingStatus

    read_books = db.query(Book).join(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.status == ReadingStatus.COMPLETED
    ).all()

    if not read_books:
        return get_trending_books(count, db, current_user)

    read_book_ids = [book.id for book in read_books]
    read_categories_subquery = db.query(book_category.c.category_id).filter(
        book_category.c.book_id.in_(read_book_ids)
    ).distinct().subquery()

    recommended_books = db.query(Book).join(
        book_category, Book.id == book_category.c.book_id
    ).filter(
        book_category.c.category_id.in_(db.query(read_categories_subquery.c.category_id)),
        ~Book.id.in_(read_book_ids)
    ).distinct().order_by(Book.rating.desc().nullslast()).limit(count).all()

    return recommended_books


@router.get("/similar/{book_id}", response_model=List[BookSchema])
def get_similar_books(
    book_id: UUID,
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return []

    category_ids = db.query(book_category.c.category_id).filter(
        book_category.c.book_id == book_id
    ).all()
    category_ids = [row[0] for row in category_ids]

    query = db.query(Book).filter(Book.id != book_id)
    filters = []
    if book.author:
        filters.append(Book.author == book.author)
    if category_ids:
        filters.append(Book.id.in_(
            db.query(book_category.c.book_id).filter(book_category.c.category_id.in_(category_ids))
        ))

    if not filters:
        return []

    # `.distinct()` would force PG to emit DISTINCT on every selected
    # column, including the JSON `tags`/`book_metadata` columns which
    # have no equality operator in PostgreSQL ("could not identify an
    # equality operator for type json"). Dedup on `id` instead via a
    # subquery so the JSON fields never participate in DISTINCT.
    similar_ids = (
        query.filter(or_(*filters))
        .with_entities(Book.id)
        .distinct()
        .subquery()
    )
    similar_books = (
        db.query(Book)
        .filter(Book.id.in_(similar_ids))
        .order_by(Book.rating.desc().nullslast())
        .limit(count)
        .all()
    )
    return similar_books
