from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.annotation import Annotation, Bookmark
from app.models.user import User


class BookmarkService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, book_id: UUID, user: User) -> tuple[list[Bookmark], int]:
        q = (
            self.db.query(Bookmark)
            .filter(Bookmark.user_id == user.id, Bookmark.book_id == book_id)
            .order_by(Bookmark.created_at.desc())
        )
        rows = q.all()
        return rows, len(rows)

    def create(self, book_id: UUID, user: User, payload: dict) -> Bookmark:
        row = Bookmark(user_id=user.id, book_id=book_id, **payload)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_owned(self, bookmark_id: UUID, user: User) -> Optional[Bookmark]:
        return (
            self.db.query(Bookmark)
            .filter(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)
            .first()
        )

    def update(self, bookmark_id: UUID, user: User, payload: dict) -> Optional[Bookmark]:
        row = self.get_owned(bookmark_id, user)
        if row is None:
            return None
        for k, v in payload.items():
            setattr(row, k, v)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, bookmark_id: UUID, user: User) -> bool:
        row = self.get_owned(bookmark_id, user)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True


class AnnotationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, book_id: UUID, user: User) -> tuple[list[Annotation], int]:
        q = (
            self.db.query(Annotation)
            .filter(Annotation.user_id == user.id, Annotation.book_id == book_id)
            .order_by(Annotation.created_at.desc())
        )
        rows = q.all()
        return rows, len(rows)

    def create(self, book_id: UUID, user: User, payload: dict) -> Annotation:
        row = Annotation(user_id=user.id, book_id=book_id, **payload)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_owned(self, annotation_id: UUID, user: User) -> Optional[Annotation]:
        return (
            self.db.query(Annotation)
            .filter(Annotation.id == annotation_id, Annotation.user_id == user.id)
            .first()
        )

    def update(self, annotation_id: UUID, user: User, payload: dict) -> Optional[Annotation]:
        row = self.get_owned(annotation_id, user)
        if row is None:
            return None
        for k, v in payload.items():
            setattr(row, k, v)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, annotation_id: UUID, user: User) -> bool:
        row = self.get_owned(annotation_id, user)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
