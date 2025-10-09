from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db.base import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.scanner_service import BookScanner
from app.services.metadata_service import OnlineMetadataService
from app.services.cover_service import CoverService
from app.core.config import settings

router = APIRouter(prefix="/scanner", tags=["Scanner"])

class ScanRequest(BaseModel):
    directory: str
    
class ScanFileRequest(BaseModel):
    file_path: str

class SyncMetadataRequest(BaseModel):
    book_id: str
    force: bool = False

@router.post("/scan-directory")
def scan_directory(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    扫描指定目录中的所有书籍文件
    """
    scanner = BookScanner(db)
    
    try:
        # 在后台任务中执行扫描（避免超时）
        stats = scanner.scan_directory(request.directory)
        
        return {
            "message": "Directory scanned successfully",
            "stats": stats
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning directory: {str(e)}"
        )

@router.post("/scan-file")
def scan_file(
    request: ScanFileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    扫描单个文件并添加到图书馆
    """
    scanner = BookScanner(db)
    
    try:
        book = scanner.scan_single_file(request.file_path)
        
        if book:
            return {
                "message": "File scanned successfully",
                "book_id": str(book.id),
                "title": book.title
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to scan file"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning file: {str(e)}"
        )

@router.post("/sync-metadata/{book_id}")
async def sync_metadata(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从在线源同步书籍元数据
    """
    from app.models.book import Book
    from uuid import UUID
    
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book ID format"
        )
    
    book = db.query(Book).filter(Book.id == book_uuid).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    online_service = OnlineMetadataService()
    cover_service = CoverService(settings.UPLOADS_DIR)
    
    # 尝试从豆瓣获取
    metadata = None
    if book.isbn:
        metadata = await online_service.fetch_from_douban(isbn=book.isbn)
    
    if not metadata and book.title:
        metadata = await online_service.fetch_from_douban(title=book.title)
    
    # 如果豆瓣没有，尝试Google Books
    if not metadata and book.isbn:
        metadata = await online_service.fetch_from_google_books(
            isbn=book.isbn,
            api_key=settings.GOOGLE_BOOKS_API_KEY
        )
    
    if metadata:
        # 更新书籍信息
        if metadata.get('title'):
            book.title = metadata['title']
        if metadata.get('subtitle'):
            book.subtitle = metadata['subtitle']
        if metadata.get('author'):
            book.author = metadata['author']
        if metadata.get('publisher'):
            book.publisher = metadata['publisher']
        if metadata.get('description'):
            book.description = metadata['description']
        if metadata.get('isbn'):
            book.isbn = metadata['isbn']
        if metadata.get('rating'):
            book.rating = float(metadata['rating'])
        if metadata.get('rating_count'):
            book.rating_count = int(metadata['rating_count'])
        if metadata.get('tags'):
            book.tags = metadata['tags']
        
        # 下载封面
        if metadata.get('cover_url') and not book.cover_url:
            cover_path = await cover_service.download_cover(
                metadata['cover_url'],
                str(book.id)
            )
            if cover_path:
                book.cover_url = cover_path
        
        db.commit()
        db.refresh(book)
        
        return {
            "message": "Metadata synced successfully",
            "book": {
                "id": str(book.id),
                "title": book.title,
                "author": book.author,
                "cover_url": book.cover_url
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metadata found online"
        )

@router.post("/extract-cover/{book_id}")
def extract_cover(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从书籍文件中提取封面
    """
    from app.models.book import Book, FileFormat
    from uuid import UUID
    
    try:
        book_uuid = UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book ID format"
        )
    
    book = db.query(Book).filter(Book.id == book_uuid).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    cover_service = CoverService(settings.UPLOADS_DIR)
    cover_path = None
    
    if book.file_format == FileFormat.PDF:
        cover_path = cover_service.extract_cover_from_pdf(book.file_path, str(book.id))
    elif book.file_format == FileFormat.EPUB:
        cover_path = cover_service.extract_cover_from_epub(book.file_path, str(book.id))
    
    if cover_path:
        book.cover_url = cover_path
        db.commit()
        
        return {
            "message": "Cover extracted successfully",
            "cover_url": cover_path
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract cover"
        )
