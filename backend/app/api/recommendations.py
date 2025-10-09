from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.db.base import get_db
from app.schemas.book import Book as BookSchema
from app.models.book import Book, Category
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/random", response_model=List[BookSchema])
def get_random_recommendations(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    随机推荐书籍
    
    优先推荐高评分书籍
    """
    # 获取有评分的书籍，按评分排序后随机选择
    books = db.query(Book)\
        .filter(Book.rating.isnot(None))\
        .order_by(Book.rating.desc())\
        .limit(count * 2)\
        .all()
    
    if not books:
        # 如果没有评分书籍，就从所有书籍中随机选择
        books = db.query(Book).order_by(func.random()).limit(count).all()
    else:
        # 从高评分书籍中随机选择
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
    """
    基于分类的推荐
    
    返回指定分类中的热门书籍
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return []
    
    # 从该分类中选择评分最高的书籍
    books = [book for book in category.books if book.rating]
    books.sort(key=lambda x: x.rating or 0, reverse=True)
    
    return books[:count]

@router.get("/trending", response_model=List[BookSchema])
def get_trending_books(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    热门推荐
    
    基于评分和评分人数
    """
    books = db.query(Book)\
        .filter(Book.rating.isnot(None))\
        .filter(Book.rating_count.isnot(None))\
        .order_by(Book.rating.desc(), Book.rating_count.desc())\
        .limit(count)\
        .all()
    
    return books

@router.get("/personalized", response_model=List[BookSchema])
def get_personalized_recommendations(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    个性化推荐
    
    基于用户的阅读历史（当前版本简化实现）
    """
    from app.models.reading import ReadingProgress, ReadingStatus
    
    # 获取用户已读书籍
    read_books = db.query(Book)\
        .join(ReadingProgress)\
        .filter(ReadingProgress.user_id == current_user.id)\
        .filter(ReadingProgress.status == ReadingStatus.COMPLETED)\
        .all()
    
    if not read_books:
        # 如果用户没有阅读历史，返回热门推荐
        return get_trending_books(count, db, current_user)
    
    # 收集已读书籍的分类
    read_categories = set()
    for book in read_books:
        for category in book.categories:
            read_categories.add(category.id)
    
    # 推荐相同分类的其他书籍
    recommended_books = []
    read_book_ids = {book.id for book in read_books}
    
    for category_id in read_categories:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            for book in category.books:
                if book.id not in read_book_ids and book not in recommended_books:
                    recommended_books.append(book)
    
    # 按评分排序
    recommended_books.sort(key=lambda x: x.rating or 0, reverse=True)
    
    return recommended_books[:count]

@router.get("/similar/{book_id}", response_model=List[BookSchema])
def get_similar_books(
    book_id: UUID,
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    相似书籍推荐
    
    基于相同作者或相同分类
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return []
    
    similar_books = []
    
    # 1. 相同作者的其他书籍
    if book.author:
        author_books = db.query(Book)\
            .filter(Book.author == book.author)\
            .filter(Book.id != book_id)\
            .all()
        similar_books.extend(author_books)
    
    # 2. 相同分类的其他书籍
    for category in book.categories:
        for cat_book in category.books:
            if cat_book.id != book_id and cat_book not in similar_books:
                similar_books.append(cat_book)
    
    # 按评分排序
    similar_books.sort(key=lambda x: x.rating or 0, reverse=True)
    
    return similar_books[:count]
