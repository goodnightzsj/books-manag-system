import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import magic
from sqlalchemy.orm import Session

from app.models.book import Book, FileFormat
from app.services.metadata_service import MetadataExtractor

class BookScanner:
    """书籍文件扫描服务"""
    
    SUPPORTED_FORMATS = {
        '.pdf': FileFormat.PDF,
        '.epub': FileFormat.EPUB,
        '.mobi': FileFormat.MOBI,
        '.azw3': FileFormat.AZW3,
        '.txt': FileFormat.TXT,
        '.djvu': FileFormat.DJVU
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.metadata_extractor = MetadataExtractor()
    
    def scan_directory(self, directory_path: str) -> Dict[str, any]:
        """
        扫描指定目录，发现所有电子书文件
        
        Args:
            directory_path: 要扫描的目录路径
            
        Returns:
            扫描结果统计
        """
        if not os.path.exists(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"Not a directory: {directory_path}")
        
        stats = {
            'total_files': 0,
            'new_books': 0,
            'updated_books': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # 递归扫描目录
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                # 检查文件格式是否支持
                if file_ext not in self.SUPPORTED_FORMATS:
                    stats['skipped'] += 1
                    continue
                
                stats['total_files'] += 1
                
                try:
                    # 处理单个文件
                    result = self._process_file(file_path, file_ext)
                    if result == 'new':
                        stats['new_books'] += 1
                    elif result == 'updated':
                        stats['updated_books'] += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
                    stats['errors'] += 1
        
        return stats
    
    def _process_file(self, file_path: str, file_ext: str) -> str:
        """
        处理单个文件
        
        Returns:
            'new': 新增书籍
            'updated': 更新书籍
            'skipped': 跳过
        """
        # 计算文件哈希（用于检测重复）
        file_hash = self._calculate_file_hash(file_path)
        
        # 检查是否已存在
        existing_book = self.db.query(Book).filter(
            Book.file_path == file_path
        ).first()
        
        if existing_book:
            # 检查文件是否被修改
            file_size = os.path.getsize(file_path)
            if existing_book.file_size == file_size:
                return 'skipped'
        
        # 提取元数据
        metadata = self.metadata_extractor.extract(file_path, file_ext)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_format = self.SUPPORTED_FORMATS[file_ext]
        
        if existing_book:
            # 更新现有书籍
            existing_book.title = metadata.get('title', existing_book.title)
            existing_book.author = metadata.get('author', existing_book.author)
            existing_book.description = metadata.get('description', existing_book.description)
            existing_book.publisher = metadata.get('publisher', existing_book.publisher)
            existing_book.isbn = metadata.get('isbn', existing_book.isbn)
            existing_book.language = metadata.get('language', existing_book.language)
            existing_book.page_count = metadata.get('page_count', existing_book.page_count)
            existing_book.file_size = file_size
            existing_book.indexed_at = datetime.utcnow()
            existing_book.updated_at = datetime.utcnow()
            
            self.db.commit()
            return 'updated'
        else:
            # 创建新书籍
            book = Book(
                title=metadata.get('title', Path(file_path).stem),
                author=metadata.get('author'),
                description=metadata.get('description'),
                publisher=metadata.get('publisher'),
                isbn=metadata.get('isbn'),
                language=metadata.get('language', 'zh'),
                page_count=metadata.get('page_count'),
                file_path=file_path,
                file_format=file_format,
                file_size=file_size,
                indexed_at=datetime.utcnow()
            )
            
            self.db.add(book)
            self.db.commit()
            return 'new'
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            # 只读取前1MB用于哈希计算（提高性能）
            chunk = f.read(1024 * 1024)
            hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def scan_single_file(self, file_path: str) -> Optional[Book]:
        """
        扫描单个文件并添加到数据库
        
        Args:
            file_path: 文件路径
            
        Returns:
            创建的Book对象，如果失败返回None
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {file_ext}")
        
        try:
            result = self._process_file(file_path, file_ext)
            if result in ['new', 'updated']:
                return self.db.query(Book).filter(Book.file_path == file_path).first()
        except Exception as e:
            print(f"Error scanning file {file_path}: {str(e)}")
            raise
        
        return None
