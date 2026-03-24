from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.base import get_db
from app.models.book import Book
from app.models.user import User
from app.services.file_access_service import FileAccessService

router = APIRouter(prefix="/files", tags=["Files"])

CHUNK_SIZE = 1024 * 1024


def _sanitize_filename(filename: str) -> str:
    return "".join(char for char in filename if char.isalnum() or char in (" ", ".", "_", "-"))


def _get_book_or_404(db: Session, book_id: UUID) -> Book:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def _resolve_book_file(book: Book) -> str:
    try:
        return FileAccessService().resolve_book_file(book.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book file not found on server") from exc


def _resolve_upload_file(upload_url: str) -> str:
    uploads_root = Path(settings.UPLOADS_DIR).resolve()
    candidate = (uploads_root / upload_url.removeprefix("/uploads/")).resolve()
    if uploads_root not in candidate.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover file not found")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover file not found")
    return str(candidate)


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    if not range_header.startswith("bytes="):
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid Range header")

    raw_range = range_header[len("bytes=") :]
    if "," in raw_range:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Multiple ranges not supported")

    try:
        start_text, end_text = raw_range.split("-", 1)
        if start_text == "":
            suffix_length = int(end_text)
            if suffix_length <= 0:
                raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid Range header")
            start = max(file_size - suffix_length, 0)
            end = file_size - 1
            return start, end

        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid Range header") from exc

    if start < 0 or end < start or start >= file_size:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Range out of bounds")
    return start, min(end, file_size - 1)


def _iter_file_range(file_path: str, start: int, end: int):
    remaining = end - start + 1
    with open(file_path, mode="rb") as file:
        file.seek(start)
        while remaining > 0:
            chunk = file.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/download/{book_id}")
def download_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = _get_book_or_404(db, book_id)
    file_path = _resolve_book_file(book)
    filename = _sanitize_filename(f"{book.title}.{book.file_format.value}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/stream/{book_id}")
def stream_book(
    book_id: UUID,
    range_header: str | None = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = _get_book_or_404(db, book_id)
    file_path = _resolve_book_file(book)
    media_type = FileAccessService().guess_media_type(book.file_format.value)
    filename = _sanitize_filename(f"{book.title}.{book.file_format.value}")
    file_size = Path(file_path).stat().st_size

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{filename}"',
    }

    if not range_header:
        headers["Content-Length"] = str(file_size)
        return StreamingResponse(
            _iter_file_range(file_path, 0, file_size - 1),
            media_type=media_type,
            headers=headers,
        )

    start, end = _parse_range_header(range_header, file_size)
    content_length = end - start + 1
    headers.update(
        {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
        }
    )
    return StreamingResponse(
        _iter_file_range(file_path, start, end),
        media_type=media_type,
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
    )


@router.head("/stream/{book_id}")
def head_stream_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = _get_book_or_404(db, book_id)
    file_path = _resolve_book_file(book)
    file_size = Path(file_path).stat().st_size
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": FileAccessService().guess_media_type(book.file_format.value),
        },
    )


@router.get("/cover/{book_id}")
def get_book_cover(
    book_id: UUID,
    db: Session = Depends(get_db),
):
    book = _get_book_or_404(db, book_id)
    if not book.cover_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book cover not available")

    full_path = Path(_resolve_upload_file(book.cover_url))

    media_type = "image/png" if full_path.suffix.lower() == ".png" else "image/jpeg"
    if full_path.suffix.lower() == ".webp":
        media_type = "image/webp"

    return FileResponse(path=str(full_path), media_type=media_type)
