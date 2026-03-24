from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.note import BookNoteCreate, BookNoteListResponse, BookNoteResponse, BookNoteUpdate
from app.services.note_service import NoteService

router = APIRouter(prefix="/books/{book_id}/notes", tags=["Notes"])


@router.get("", response_model=BookNoteListResponse)
def list_notes(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = NoteService(db).list_for_book(book_id=book_id, user=current_user)
    return {"items": items, "total": total}


@router.post("", response_model=BookNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    book_id: UUID,
    note_data: BookNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return NoteService(db).create_for_book(
            book_id=book_id,
            user=current_user,
            payload=note_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{note_id}", response_model=BookNoteResponse)
def update_note(
    book_id: UUID,
    note_id: UUID,
    note_data: BookNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return NoteService(db).update_note(
            book_id=book_id,
            note_id=note_id,
            user=current_user,
            payload=note_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    book_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        NoteService(db).delete_note(book_id=book_id, note_id=note_id, user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
