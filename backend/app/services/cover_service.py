import os
from pathlib import Path
from typing import Optional
from PIL import Image
import io
import httpx

class CoverService:
    """封面处理服务"""
    
    def __init__(self, upload_dir: str = "/app/uploads"):
        self.upload_dir = upload_dir
        self.covers_dir = os.path.join(upload_dir, "covers")
        self.thumbnails_dir = os.path.join(upload_dir, "thumbnails")
        
        # 创建目录
        os.makedirs(self.covers_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
    
    def extract_cover_from_pdf(self, pdf_path: str, book_id: str) -> Optional[str]:
        """
        从PDF中提取封面（第一页）
        
        Args:
            pdf_path: PDF文件路径
            book_id: 书籍ID
            
        Returns:
            封面图片路径
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                # 获取第一页
                page = doc[0]
                
                # 渲染为图片
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放提高质量
                
                # 保存封面
                cover_filename = f"{book_id}_cover.png"
                cover_path = os.path.join(self.covers_dir, cover_filename)
                pix.save(cover_path)
                
                # 生成缩略图
                self._generate_thumbnail(cover_path, book_id)
                
                return f"/uploads/covers/{cover_filename}"
        except Exception as e:
            print(f"Error extracting PDF cover: {str(e)}")
        
        return None
    
    def extract_cover_from_epub(self, epub_path: str, book_id: str) -> Optional[str]:
        """
        从EPUB中提取封面
        
        Args:
            epub_path: EPUB文件路径
            book_id: 书籍ID
            
        Returns:
            封面图片路径
        """
        try:
            import ebookmeta
            
            epub = ebookmeta.get_metadata(epub_path)
            
            if epub and epub.cover_image_content:
                # 保存封面
                cover_filename = f"{book_id}_cover.jpg"
                cover_path = os.path.join(self.covers_dir, cover_filename)
                
                with open(cover_path, 'wb') as f:
                    f.write(epub.cover_image_content)
                
                # 生成缩略图
                self._generate_thumbnail(cover_path, book_id)
                
                return f"/uploads/covers/{cover_filename}"
        except Exception as e:
            print(f"Error extracting EPUB cover: {str(e)}")
        
        return None
    
    async def download_cover(self, url: str, book_id: str) -> Optional[str]:
        """
        从URL下载封面图片
        
        Args:
            url: 封面图片URL
            book_id: 书籍ID
            
        Returns:
            本地封面路径
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                
                if response.status_code == 200:
                    # 确定文件扩展名
                    content_type = response.headers.get('content-type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = 'jpg'
                    elif 'png' in content_type:
                        ext = 'png'
                    else:
                        ext = 'jpg'  # 默认
                    
                    # 保存封面
                    cover_filename = f"{book_id}_cover.{ext}"
                    cover_path = os.path.join(self.covers_dir, cover_filename)
                    
                    with open(cover_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 生成缩略图
                    self._generate_thumbnail(cover_path, book_id)
                    
                    return f"/uploads/covers/{cover_filename}"
        except Exception as e:
            print(f"Error downloading cover from {url}: {str(e)}")
        
        return None
    
    def _generate_thumbnail(self, image_path: str, book_id: str, size: tuple = (200, 300)):
        """
        生成缩略图
        
        Args:
            image_path: 原图路径
            book_id: 书籍ID
            size: 缩略图尺寸 (width, height)
        """
        try:
            with Image.open(image_path) as img:
                # 保持宽高比缩放
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 保存缩略图
                ext = Path(image_path).suffix
                thumbnail_filename = f"{book_id}_thumb{ext}"
                thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
                
                img.save(thumbnail_path, quality=85, optimize=True)
        except Exception as e:
            print(f"Error generating thumbnail: {str(e)}")
    
    def get_cover_path(self, book_id: str) -> Optional[str]:
        """
        获取书籍封面路径
        
        Args:
            book_id: 书籍ID
            
        Returns:
            封面URL路径
        """
        # 检查可能的文件扩展名
        for ext in ['jpg', 'jpeg', 'png']:
            filename = f"{book_id}_cover.{ext}"
            full_path = os.path.join(self.covers_dir, filename)
            if os.path.exists(full_path):
                return f"/uploads/covers/{filename}"
        
        return None
    
    def get_thumbnail_path(self, book_id: str) -> Optional[str]:
        """
        获取缩略图路径
        
        Args:
            book_id: 书籍ID
            
        Returns:
            缩略图URL路径
        """
        # 检查可能的文件扩展名
        for ext in ['jpg', 'jpeg', 'png']:
            filename = f"{book_id}_thumb.{ext}"
            full_path = os.path.join(self.thumbnails_dir, filename)
            if os.path.exists(full_path):
                return f"/uploads/thumbnails/{filename}"
        
        return None
