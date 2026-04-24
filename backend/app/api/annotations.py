from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationListResponse,
    AnnotationResponse,
    AnnotationUpdate,
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
    BookmarkUpdate,
)
from app.services.annotation_service import AnnotationService, BookmarkService

router = APIRouter(tags=["Annotations"])


@router.get(
    "/books/{book_id}/bookmarks",
    response_model=BookmarkListResponse,
)
def list_bookmarks(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = BookmarkService(db).list_for_user(book_id=book_id, user=current_user)
    return BookmarkListResponse(items=items, total=total)


@router.post(
    "/books/{book_id}/bookmarks",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    book_id: UUID,
    payload: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BookmarkService(db).create(
        book_id=book_id,
        user=current_user,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.put(
    "/books/{book_id}/bookmarks/{bookmark_id}",
    response_model=BookmarkResponse,
)
def update_bookmark(
    book_id: UUID,
    bookmark_id: UUID,
    payload: BookmarkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = BookmarkService(db).update(
        bookmark_id=bookmark_id,
        user=current_user,
        payload=payload.model_dump(exclude_unset=True),
    )
    if row is None or row.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return row


@router.delete(
    "/books/{book_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bookmark(
    book_id: UUID,
    bookmark_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = BookmarkService(db).get_owned(bookmark_id, current_user)
    if row is None or row.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    BookmarkService(db).delete(bookmark_id, current_user)


@router.get(
    "/books/{book_id}/annotations",
    response_model=AnnotationListResponse,
)
def list_annotations(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = AnnotationService(db).list_for_user(book_id=book_id, user=current_user)
    return AnnotationListResponse(items=items, total=total)


@router.post(
    "/books/{book_id}/annotations",
    response_model=AnnotationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_annotation(
    book_id: UUID,
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnnotationService(db).create(
        book_id=book_id,
        user=current_user,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.put(
    "/books/{book_id}/annotations/{annotation_id}",
    response_model=AnnotationResponse,
)
def update_annotation(
    book_id: UUID,
    annotation_id: UUID,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = AnnotationService(db).update(
        annotation_id=annotation_id,
        user=current_user,
        payload=payload.model_dump(exclude_unset=True),
    )
    if row is None or row.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    return row


@router.delete(
    "/books/{book_id}/annotations/{annotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_annotation(
    book_id: UUID,
    annotation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = AnnotationService(db).get_owned(annotation_id, current_user)
    if row is None or row.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    AnnotationService(db).delete(annotation_id, current_user)
