import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from app.core.config import settings
from app.models.book import Book, FileFormat
from app.services.file_access_service import FileAccessService

logger = logging.getLogger(__name__)


class CoverService:
    def __init__(self, upload_dir: str | None = None):
        base_dir = Path(upload_dir or settings.UPLOADS_DIR)
        self.upload_dir = base_dir
        self.covers_dir = base_dir / "covers"
        self.thumbnails_dir = base_dir / "thumbnails"
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    def ensure_cover(
        self,
        book: Book,
        *,
        prefer_remote: bool = False,
        source_url: str | None = None,
        force: bool = False,
    ) -> str | None:
        existing = self.get_cover_path(str(book.id))
        if existing and not force:
            return existing

        cover_path = None
        if prefer_remote and source_url:
            cover_path = self.download_cover(source_url, str(book.id))
            if not cover_path:
                cover_path = self.extract_local_cover(book)
        else:
            cover_path = self.extract_local_cover(book)
            if not cover_path and source_url:
                cover_path = self.download_cover(source_url, str(book.id))

        return cover_path or existing

    def extract_local_cover(self, book: Book) -> str | None:
        try:
            file_path = FileAccessService().resolve_book_file(book.file_path)
        except Exception as exc:
            logger.error("Error resolving book file for cover extraction %s: %s", book.id, exc)
            return None

        if book.file_format == FileFormat.PDF:
            return self.extract_cover_from_pdf(file_path, str(book.id))
        if book.file_format == FileFormat.EPUB:
            return self.extract_cover_from_epub(file_path, str(book.id))
        return None

    def extract_cover_from_pdf(self, pdf_path: str, book_id: str) -> str | None:
        try:
            import fitz

            document = fitz.open(pdf_path)
            if len(document) == 0:
                return None
            page = document[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            cover_path = self.covers_dir / f"{book_id}_cover.png"
            pix.save(cover_path)
            self._generate_thumbnail(cover_path, book_id)
            return f"/uploads/covers/{cover_path.name}"
        except Exception as exc:
            logger.error("Error extracting PDF cover: %s", exc)
            return None

    def extract_cover_from_epub(self, epub_path: str, book_id: str) -> str | None:
        try:
            import ebookmeta

            epub = ebookmeta.get_metadata(epub_path)
            if not epub or not epub.cover_image_content:
                return None
            cover_path = self.covers_dir / f"{book_id}_cover.jpg"
            cover_path.write_bytes(epub.cover_image_content)
            self._generate_thumbnail(cover_path, book_id)
            return f"/uploads/covers/{cover_path.name}"
        except Exception as exc:
            logger.error("Error extracting EPUB cover: %s", exc)
            return None

    def download_cover(self, url: str, book_id: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            logger.error("Unsupported cover URL scheme: %s", url)
            return None

        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(url, timeout=30)
                if response.status_code != 200:
                    return None
                suffix = self._guess_suffix(response.headers.get("content-type", ""), url)
                cover_path = self.covers_dir / f"{book_id}_cover{suffix}"
                cover_path.write_bytes(response.content)
                self._generate_thumbnail(cover_path, book_id)
                return f"/uploads/covers/{cover_path.name}"
        except Exception as exc:
            logger.error("Error downloading cover from %s: %s", url, exc)
            return None

    def get_cover_path(self, book_id: str) -> str | None:
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            cover_path = self.covers_dir / f"{book_id}_cover{ext}"
            if cover_path.exists():
                return f"/uploads/covers/{cover_path.name}"
        return None

    def get_thumbnail_path(self, book_id: str) -> str | None:
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            thumbnail_path = self.thumbnails_dir / f"{book_id}_thumb{ext}"
            if thumbnail_path.exists():
                return f"/uploads/thumbnails/{thumbnail_path.name}"
        return None

    def _generate_thumbnail(self, image_path: Path, book_id: str, size: tuple[int, int] = (200, 300)) -> None:
        try:
            with Image.open(image_path) as image:
                image.thumbnail(size, Image.Resampling.LANCZOS)
                thumbnail_path = self.thumbnails_dir / f"{book_id}_thumb{image_path.suffix}"
                image.save(thumbnail_path, quality=85, optimize=True)
        except Exception as exc:
            logger.error("Error generating thumbnail: %s", exc)

    def _guess_suffix(self, content_type: str, url: str) -> str:
        normalized = content_type.lower()
        if "png" in normalized:
            return ".png"
        if "webp" in normalized:
            return ".webp"
        if "jpeg" in normalized or "jpg" in normalized:
            return ".jpg"

        parsed = Path(urlparse(url).path).suffix.lower()
        if parsed in {".jpg", ".jpeg", ".png", ".webp"}:
            return parsed
        return ".jpg"
