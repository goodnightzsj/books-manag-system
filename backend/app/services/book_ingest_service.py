from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book, FileFormat, HashStatus, book_category
from app.models.note import BookNote
from app.models.reading import ReadingProgress
from app.models.scan_job import ScanJobItem
from app.services.hash_service import HashDecision, HashService


@dataclass(slots=True)
class BookUpsertResult:
    book_id: UUID
    action: Literal["created", "updated", "skipped"]
    should_hash: bool
    should_extract_cover: bool


class BookIngestService:
    MERGEABLE_BOOK_FIELDS = (
        "subtitle",
        "author",
        "publisher",
        "publish_date",
        "description",
        "isbn",
        "cover_url",
        "language",
        "page_count",
        "rating",
        "rating_count",
        "tags",
        "book_metadata",
        "source_provider",
        "metadata_synced_at",
    )

    def __init__(self, db: Session, hash_service: HashService | None = None):
        self.db = db
        self.hash_service = hash_service or HashService()

    def upsert_scanned_book(self, *, file_path: str, file_format: str, file_size: int, file_mtime: datetime, metadata: dict[str, Any]) -> BookUpsertResult:
        existing_book = self.db.query(Book).filter(Book.file_path == file_path).first()
        hash_decision = self.hash_service.should_hash(
            existing_book,
            file_path=file_path,
            file_size=file_size,
            file_mtime=file_mtime,
        )
        same_snapshot = existing_book is not None and existing_book.file_size == file_size and self._same_mtime(existing_book.file_mtime, file_mtime)

        if existing_book and same_snapshot:
            existing_book.file_size = file_size
            existing_book.file_mtime = file_mtime
            existing_book.updated_at = datetime.utcnow()
            self._apply_hash_decision(existing_book, hash_decision, clear_existing=False)
            return BookUpsertResult(
                book_id=existing_book.id,
                action="skipped",
                should_hash=hash_decision.should_hash,
                should_extract_cover=False,
            )

        if existing_book:
            existing_book.title = metadata.get("title", existing_book.title)
            existing_book.author = metadata.get("author", existing_book.author)
            existing_book.description = metadata.get("description", existing_book.description)
            existing_book.publisher = metadata.get("publisher", existing_book.publisher)
            existing_book.isbn = metadata.get("isbn", existing_book.isbn)
            existing_book.language = metadata.get("language", existing_book.language)
            existing_book.page_count = metadata.get("page_count", existing_book.page_count)
            existing_book.file_size = file_size
            existing_book.file_mtime = file_mtime
            existing_book.indexed_at = datetime.utcnow()
            existing_book.updated_at = datetime.utcnow()
            self._apply_hash_decision(existing_book, hash_decision, clear_existing=True)
            return BookUpsertResult(
                book_id=existing_book.id,
                action="updated",
                should_hash=hash_decision.should_hash,
                should_extract_cover=file_format in {FileFormat.PDF.value, FileFormat.EPUB.value},
            )

        book = Book(
            title=metadata.get("title", Path(file_path).stem),
            author=metadata.get("author"),
            description=metadata.get("description"),
            publisher=metadata.get("publisher"),
            isbn=metadata.get("isbn"),
            language=metadata.get("language", "zh"),
            page_count=metadata.get("page_count"),
            file_path=file_path,
            file_format=FileFormat(file_format),
            file_size=file_size,
            file_mtime=file_mtime,
            indexed_at=datetime.utcnow(),
            hash_status=hash_decision.next_status,
            hash_error=None,
        )
        self.db.add(book)
        self.db.flush()
        return BookUpsertResult(
            book_id=book.id,
            action="created",
            should_hash=hash_decision.should_hash,
            should_extract_cover=file_format in {FileFormat.PDF.value, FileFormat.EPUB.value},
        )

    def apply_hash_result(self, *, book_id: UUID, content_hash: str, algorithm: str, item_id: UUID | None = None) -> Book:
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError(f"Book not found: {book_id}")

        if item_id is not None:
            item = self.db.query(ScanJobItem).filter(ScanJobItem.id == item_id).first()
            if item:
                item.detected_hash = content_hash

        duplicates = (
            self.db.query(Book)
            .filter(Book.content_hash == content_hash, Book.id != book_id)
            .order_by(Book.created_at.asc(), Book.id.asc())
            .all()
        )
        if not duplicates:
            book.content_hash = content_hash
            book.hash_algorithm = algorithm
            book.hash_status = HashStatus.DONE
            book.hash_error = None
            book.updated_at = datetime.utcnow()
            return book

        canonical = self._select_canonical_book([book, *duplicates])
        if canonical.id == book.id:
            for duplicate in duplicates:
                self.merge_duplicate_books(canonical.id, duplicate.id)
            self.db.flush()
            canonical.content_hash = content_hash
            canonical.hash_algorithm = algorithm
            canonical.hash_status = HashStatus.DONE
            canonical.hash_error = None
            canonical.updated_at = datetime.utcnow()
            return canonical

        canonical.content_hash = content_hash
        canonical.hash_algorithm = algorithm
        canonical.hash_status = HashStatus.DONE
        canonical.hash_error = None
        canonical.updated_at = datetime.utcnow()
        self.merge_duplicate_books(canonical.id, book.id)
        for duplicate in duplicates:
            if duplicate.id != canonical.id:
                self.merge_duplicate_books(canonical.id, duplicate.id)
        return canonical

    def merge_duplicate_books(self, canonical_id: UUID, duplicate_id: UUID) -> Book:
        canonical = self.db.query(Book).filter(Book.id == canonical_id).first()
        duplicate = self.db.query(Book).filter(Book.id == duplicate_id).first()
        if not canonical or not duplicate:
            raise ValueError("Canonical or duplicate book not found")
        if canonical.id == duplicate.id:
            return canonical

        self._merge_book_fields(canonical, duplicate)
        self._merge_reading_progress(canonical, duplicate)
        self.db.query(BookNote).filter(BookNote.book_id == duplicate.id).update(
            {BookNote.book_id: canonical.id},
            synchronize_session=False,
        )
        self.db.query(ScanJobItem).filter(ScanJobItem.book_id == duplicate.id).update(
            {ScanJobItem.book_id: canonical.id},
            synchronize_session=False,
        )
        canonical_categories = select(book_category.c.category_id).where(book_category.c.book_id == canonical.id)
        self.db.execute(
            book_category.delete().where(
                book_category.c.book_id == duplicate.id,
                book_category.c.category_id.in_(canonical_categories),
            )
        )
        self.db.execute(
            book_category.update().where(book_category.c.book_id == duplicate.id).values(book_id=canonical.id)
        )
        canonical.updated_at = datetime.utcnow()
        self.db.delete(duplicate)
        return canonical

    def _apply_hash_decision(self, book: Book, decision: HashDecision, *, clear_existing: bool) -> None:
        if decision.should_hash:
            if clear_existing:
                book.content_hash = None
                book.hash_algorithm = None
            book.hash_status = decision.next_status
            book.hash_error = None
            return
        book.hash_status = decision.next_status
        book.hash_error = None

    def _select_canonical_book(self, books: list[Book]) -> Book:
        return sorted(books, key=lambda book: (book.created_at or datetime.min, str(book.id)))[0]

    def _merge_book_fields(self, canonical: Book, duplicate: Book) -> None:
        if not Path(canonical.file_path).exists() and Path(duplicate.file_path).exists():
            canonical.file_path = duplicate.file_path
            canonical.file_format = duplicate.file_format
            canonical.file_size = duplicate.file_size
            canonical.file_mtime = duplicate.file_mtime

        for field_name in self.MERGEABLE_BOOK_FIELDS:
            canonical_value = getattr(canonical, field_name)
            duplicate_value = getattr(duplicate, field_name)
            if self._is_empty(canonical_value) and not self._is_empty(duplicate_value):
                setattr(canonical, field_name, duplicate_value)

        canonical.indexed_at = max(
            [value for value in [canonical.indexed_at, duplicate.indexed_at] if value is not None],
            default=canonical.indexed_at or duplicate.indexed_at,
        )

    def _merge_reading_progress(self, canonical: Book, duplicate: Book) -> None:
        duplicate_progress_rows = self.db.query(ReadingProgress).filter(ReadingProgress.book_id == duplicate.id).all()
        for duplicate_progress in duplicate_progress_rows:
            canonical_progress = (
                self.db.query(ReadingProgress)
                .filter(
                    ReadingProgress.book_id == canonical.id,
                    ReadingProgress.user_id == duplicate_progress.user_id,
                )
                .first()
            )
            if not canonical_progress:
                duplicate_progress.book_id = canonical.id
                continue
            if (duplicate_progress.updated_at or datetime.min) > (canonical_progress.updated_at or datetime.min):
                canonical_progress.current_page = duplicate_progress.current_page
                canonical_progress.total_pages = duplicate_progress.total_pages
                canonical_progress.progress_percent = duplicate_progress.progress_percent
                canonical_progress.status = duplicate_progress.status
                canonical_progress.locator = duplicate_progress.locator
                canonical_progress.started_at = duplicate_progress.started_at
                canonical_progress.finished_at = duplicate_progress.finished_at
                canonical_progress.last_read_at = duplicate_progress.last_read_at
                canonical_progress.notes = duplicate_progress.notes
                canonical_progress.bookmarks = duplicate_progress.bookmarks
                canonical_progress.updated_at = duplicate_progress.updated_at
            self.db.delete(duplicate_progress)

    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value == ""
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) == 0
        return False

    def _same_mtime(self, left: datetime | None, right: datetime | None, *, tolerance_seconds: float = 1.0) -> bool:
        if left is None or right is None:
            return False
        return abs((left - right).total_seconds()) <= tolerance_seconds
