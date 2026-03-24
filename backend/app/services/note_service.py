from uuid import UUID

from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.note import BookNote
from app.models.user import User


class NoteService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_book(self, *, book_id: UUID, user: User) -> tuple[list[BookNote], int]:
        query = (
            self.db.query(BookNote)
            .filter(BookNote.book_id == book_id, BookNote.user_id == user.id)
            .order_by(BookNote.updated_at.desc(), BookNote.created_at.desc())
        )
        return query.all(), query.count()

    def create_for_book(self, *, book_id: UUID, user: User, payload: dict) -> BookNote:
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError("Book not found")
        note = BookNote(book_id=book_id, user_id=user.id, **payload)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def update_note(self, *, book_id: UUID, note_id: UUID, user: User, payload: dict) -> BookNote:
        note = self._get_owned_note(book_id=book_id, note_id=note_id, user=user)
        if note is None:
            raise ValueError("Note not found")
        for field, value in payload.items():
            setattr(note, field, value)
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete_note(self, *, book_id: UUID, note_id: UUID, user: User) -> None:
        note = self._get_owned_note(book_id=book_id, note_id=note_id, user=user)
        if note is None:
            raise ValueError("Note not found")
        self.db.delete(note)
        self.db.commit()

    def _get_owned_note(self, *, book_id: UUID, note_id: UUID, user: User) -> BookNote | None:
        return (
            self.db.query(BookNote)
            .filter(
                BookNote.id == note_id,
                BookNote.book_id == book_id,
                BookNote.user_id == user.id,
            )
            .first()
        )
