from typing import Literal
from uuid import UUID

from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.orm import Query, Session

from app.models.book import Book, Category, FileFormat, book_category

BookSort = Literal["relevance", "created_at", "updated_at", "title", "rating"]
SortOrder = Literal["asc", "desc"]


class BookSearchService:
    SEARCH_CONFIG = "simple"
    TRIGRAM_THRESHOLD = 0.1

    def __init__(self, db: Session):
        self.db = db

    def search_books(
        self,
        *,
        q: str | None,
        author: str | None,
        category_id: UUID | None,
        file_format: FileFormat | None,
        sort: BookSort | None,
        order: SortOrder,
        page: int,
        page_size: int,
    ) -> tuple[list[Book], int]:
        query: Query = self.db.query(Book)

        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))

        if category_id:
            query = query.join(book_category, Book.id == book_category.c.book_id).filter(
                book_category.c.category_id == category_id
            )

        if file_format:
            query = query.filter(Book.file_format == file_format)

        rank_expr = None
        normalized_q = q.strip() if q else None
        if normalized_q:
            query, rank_expr = self._apply_text_search(query, normalized_q)

        total = query.count()
        resolved_sort: BookSort = sort or ("relevance" if normalized_q else "updated_at")
        query = query.order_by(*self._build_order_by(resolved_sort, order, rank_expr))
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def refresh_document(self, book_id: UUID) -> None:
        document = self._search_document_expr()
        self.db.query(Book).filter(Book.id == book_id).update(
            {Book.search_vector: func.to_tsvector(self.SEARCH_CONFIG, document)},
            synchronize_session=False,
        )

    def _apply_text_search(self, query: Query, q: str) -> tuple[Query, object]:
        document = self._search_document_expr()
        vector_expr = func.coalesce(Book.search_vector, func.to_tsvector(self.SEARCH_CONFIG, document))
        ts_query = func.plainto_tsquery(self.SEARCH_CONFIG, q)
        similarity_expr = func.greatest(
            func.similarity(func.coalesce(Book.title, ""), q),
            func.similarity(func.coalesce(Book.author, ""), q),
            func.similarity(func.coalesce(Book.publisher, ""), q),
            func.similarity(func.coalesce(Book.isbn, ""), q),
            func.similarity(func.coalesce(cast(Book.tags, Text), ""), q),
        )
        category_match_ids = select(book_category.c.book_id).join(
            Category,
            book_category.c.category_id == Category.id,
        ).where(func.similarity(func.coalesce(Category.name, ""), q) > self.TRIGRAM_THRESHOLD)
        query = query.filter(
            or_(
                vector_expr.op("@@")(ts_query),
                similarity_expr > self.TRIGRAM_THRESHOLD,
                Book.id.in_(category_match_ids),
            )
        )
        rank_expr = func.ts_rank_cd(vector_expr, ts_query) + similarity_expr
        return query, rank_expr

    def _build_order_by(self, sort: BookSort, order: SortOrder, rank_expr: object | None) -> list[object]:
        if sort == "relevance" and rank_expr is not None:
            return [rank_expr.desc(), Book.updated_at.desc(), Book.id.desc()]

        if sort == "title":
            return [Book.title.asc() if order == "asc" else Book.title.desc(), Book.id.desc()]

        if sort == "rating":
            primary = Book.rating.asc().nullslast() if order == "asc" else Book.rating.desc().nullslast()
            return [primary, Book.rating_count.desc().nullslast(), Book.id.desc()]

        column = Book.created_at if sort == "created_at" else Book.updated_at
        return [column.asc() if order == "asc" else column.desc(), Book.id.desc()]

    def _search_document_expr(self):
        return func.concat_ws(
            " ",
            func.coalesce(Book.title, ""),
            func.coalesce(Book.author, ""),
            func.coalesce(Book.isbn, ""),
            func.coalesce(Book.publisher, ""),
            func.coalesce(cast(Book.tags, Text), ""),
            func.coalesce(Book.description, ""),
        )
