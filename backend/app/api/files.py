from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import os
from pathlib import Path

from app.db.base import get_db
from app.models.book import Book
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("/download/{book_id}")
def download_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载书籍文件
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if not os.path.exists(book.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book file not found on server"
        )
    
    # 生成下载文件名
    filename = f"{book.title}.{book.file_format.value}"
    # 清理文件名中的非法字符
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-'))
    
    return FileResponse(
        path=book.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/stream/{book_id}")
async def stream_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    流式传输书籍文件（用于在线阅读）
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if not os.path.exists(book.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book file not found on server"
        )
    
    # 根据文件类型设置MIME类型
    mime_types = {
        'pdf': 'application/pdf',
        'epub': 'application/epub+zip',
        'mobi': 'application/x-mobipocket-ebook',
        'txt': 'text/plain',
    }
    
    media_type = mime_types.get(book.file_format.value, 'application/octet-stream')
    
    def iterfile():
        with open(book.file_path, mode="rb") as file:
            while chunk := file.read(1024 * 1024):  # 1MB chunks
                yield chunk
    
    return StreamingResponse(
        iterfile(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{book.title}.{book.file_format.value}"'
        }
    )

@router.get("/cover/{book_id}")
def get_book_cover(
    book_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取书籍封面（不需要认证，便于展示）
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if not book.cover_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book cover not available"
        )
    
    # 将URL路径转换为实际文件路径
    # cover_url格式: /uploads/covers/xxx.jpg
    from app.core.config import settings
    cover_path = book.cover_url.replace('/uploads/', '')
    full_path = os.path.join(settings.UPLOADS_DIR, cover_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover file not found"
        )
    
    return FileResponse(
        path=full_path,
        media_type='image/jpeg'
    )
