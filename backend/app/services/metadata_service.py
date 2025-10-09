from typing import Dict, Optional
from pathlib import Path
import os

class MetadataExtractor:
    """元数据提取服务"""
    
    def extract(self, file_path: str, file_ext: str) -> Dict[str, any]:
        """
        从文件中提取元数据
        
        Args:
            file_path: 文件路径
            file_ext: 文件扩展名（含点号，如 '.pdf'）
            
        Returns:
            包含元数据的字典
        """
        if file_ext == '.pdf':
            return self._extract_pdf(file_path)
        elif file_ext == '.epub':
            return self._extract_epub(file_path)
        elif file_ext == '.mobi':
            return self._extract_mobi(file_path)
        elif file_ext == '.txt':
            return self._extract_txt(file_path)
        else:
            return self._extract_basic(file_path)
    
    def _extract_pdf(self, file_path: str) -> Dict[str, any]:
        """提取PDF元数据"""
        metadata = {}
        
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 获取PDF信息
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    metadata['title'] = info.get('/Title', '')
                    metadata['author'] = info.get('/Author', '')
                    metadata['subject'] = info.get('/Subject', '')
                    
                # 获取页数
                metadata['page_count'] = len(pdf_reader.pages)
                
        except Exception as e:
            print(f"Error extracting PDF metadata from {file_path}: {str(e)}")
            metadata = self._extract_basic(file_path)
        
        return metadata
    
    def _extract_epub(self, file_path: str) -> Dict[str, any]:
        """提取EPUB元数据"""
        metadata = {}
        
        try:
            import ebookmeta
            
            epub = ebookmeta.get_metadata(file_path)
            
            if epub:
                metadata['title'] = epub.title or ''
                metadata['author'] = ', '.join(epub.author_list) if epub.author_list else ''
                metadata['description'] = epub.description or ''
                metadata['publisher'] = epub.publisher or ''
                metadata['isbn'] = epub.isbn or ''
                metadata['language'] = epub.language or 'zh'
                
        except Exception as e:
            print(f"Error extracting EPUB metadata from {file_path}: {str(e)}")
            metadata = self._extract_basic(file_path)
        
        return metadata
    
    def _extract_mobi(self, file_path: str) -> Dict[str, any]:
        """提取MOBI元数据"""
        metadata = {}
        
        try:
            import mobi
            
            book = mobi.extract(file_path)
            
            # MOBI元数据提取较为复杂，这里做简单处理
            # 实际项目中可能需要更完善的解析
            metadata = self._extract_basic(file_path)
            
        except Exception as e:
            print(f"Error extracting MOBI metadata from {file_path}: {str(e)}")
            metadata = self._extract_basic(file_path)
        
        return metadata
    
    def _extract_txt(self, file_path: str) -> Dict[str, any]:
        """提取TXT元数据（基本信息）"""
        metadata = self._extract_basic(file_path)
        
        try:
            # 尝试读取文件开头作为描述
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = []
                for i, line in enumerate(f):
                    if i >= 5:  # 只读前5行
                        break
                    if line.strip():
                        first_lines.append(line.strip())
                
                if first_lines:
                    metadata['description'] = ' '.join(first_lines)[:200] + '...'
        except Exception as e:
            print(f"Error reading TXT file {file_path}: {str(e)}")
        
        return metadata
    
    def _extract_basic(self, file_path: str) -> Dict[str, any]:
        """提取基本信息（从文件名）"""
        file_name = Path(file_path).stem
        
        # 尝试从文件名解析标题和作者
        # 常见格式：《书名》作者.pdf 或 书名-作者.pdf
        title = file_name
        author = None
        
        # 尝试解析《》格式
        if '《' in file_name and '》' in file_name:
            start = file_name.index('《')
            end = file_name.index('》')
            title = file_name[start+1:end]
            
            # 提取作者
            remaining = file_name[end+1:].strip()
            if remaining:
                author = remaining
        
        # 尝试解析-格式
        elif '-' in file_name:
            parts = file_name.split('-', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                author = parts[1].strip()
        
        return {
            'title': title,
            'author': author,
            'language': 'zh'
        }


class OnlineMetadataService:
    """在线元数据同步服务"""
    
    def __init__(self):
        self.douban_api_url = "https://douban.uieee.com"
    
    async def fetch_from_douban(self, isbn: str = None, title: str = None) -> Optional[Dict]:
        """
        从豆瓣API获取书籍信息
        
        Args:
            isbn: ISBN号
            title: 书名
            
        Returns:
            书籍信息字典
        """
        import httpx
        
        if not isbn and not title:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                if isbn:
                    url = f"{self.douban_api_url}/v2/book/isbn/{isbn}"
                    response = await client.get(url, timeout=10)
                else:
                    url = f"{self.douban_api_url}/v2/book/search"
                    response = await client.get(url, params={'q': title}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_douban_response(data)
        except Exception as e:
            print(f"Error fetching from Douban: {str(e)}")
        
        return None
    
    def _parse_douban_response(self, data: Dict) -> Dict:
        """解析豆瓣API响应"""
        if 'books' in data and data['books']:
            # 搜索结果
            book = data['books'][0]
        else:
            # ISBN查询结果
            book = data
        
        return {
            'title': book.get('title'),
            'subtitle': book.get('subtitle'),
            'author': ', '.join(book.get('author', [])),
            'publisher': book.get('publisher'),
            'publish_date': book.get('pubdate'),
            'isbn': book.get('isbn13') or book.get('isbn10'),
            'description': book.get('summary'),
            'cover_url': book.get('image') or book.get('images', {}).get('large'),
            'rating': book.get('rating', {}).get('average'),
            'rating_count': book.get('rating', {}).get('numRaters'),
            'tags': [tag.get('name') for tag in book.get('tags', [])]
        }
    
    async def fetch_from_google_books(self, isbn: str = None, title: str = None, 
                                      api_key: str = None) -> Optional[Dict]:
        """
        从Google Books API获取书籍信息
        
        Args:
            isbn: ISBN号
            title: 书名
            api_key: Google Books API密钥
            
        Returns:
            书籍信息字典
        """
        import httpx
        
        if not isbn and not title:
            return None
        
        base_url = "https://www.googleapis.com/books/v1/volumes"
        
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if api_key:
                    params['key'] = api_key
                
                if isbn:
                    params['q'] = f'isbn:{isbn}'
                else:
                    params['q'] = title
                
                response = await client.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('totalItems', 0) > 0:
                        return self._parse_google_books_response(data['items'][0])
        except Exception as e:
            print(f"Error fetching from Google Books: {str(e)}")
        
        return None
    
    def _parse_google_books_response(self, item: Dict) -> Dict:
        """解析Google Books API响应"""
        volume_info = item.get('volumeInfo', {})
        
        return {
            'title': volume_info.get('title'),
            'subtitle': volume_info.get('subtitle'),
            'author': ', '.join(volume_info.get('authors', [])),
            'publisher': volume_info.get('publisher'),
            'publish_date': volume_info.get('publishedDate'),
            'isbn': next((id['identifier'] for id in volume_info.get('industryIdentifiers', []) 
                         if id['type'] in ['ISBN_13', 'ISBN_10']), None),
            'description': volume_info.get('description'),
            'cover_url': volume_info.get('imageLinks', {}).get('thumbnail'),
            'page_count': volume_info.get('pageCount'),
            'language': volume_info.get('language'),
            'categories': volume_info.get('categories', [])
        }
