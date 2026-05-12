import ipaddress
import logging
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from app.core.config import settings
from app.models.book import Book, FileFormat
from app.services.file_access_service import FileAccessService

_MAX_COVER_BYTES = 16 * 1024 * 1024  # cap downloaded cover size


def _resolves_to_public_ip(host: str) -> bool:
    """True only if every resolved address for `host` is a routable public IP.

    Blocks SSRF to loopback / private / link-local / metadata endpoints when a
    metadata provider's cover_url (or a redirect) points inward.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return True

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
        # `pypdf` replaces PyMuPDF here (saves ~80 MB on disk). PDF first-page
        # rendering uses pypdf -> Pillow round trip:
        #   1. Read first XObject image embedded in page 1 (cheap, common).
        #   2. If none, ask Pillow to rasterize via the page's content stream
        #      isn't supported by pure Python; fall back to "no cover" -- the
        #      online metadata sync will usually back-fill `cover_url` anyway.
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf_path)
            if len(reader.pages) == 0:
                return None
            page = reader.pages[0]
            for image in getattr(page, "images", []):
                cover_path = self.covers_dir / f"{book_id}_cover.png"
                cover_path.write_bytes(image.data)
                self._generate_thumbnail(cover_path, book_id)
                return f"/uploads/covers/{cover_path.name}"
            return None
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
        host = parsed.hostname or ""
        if not host or not _resolves_to_public_ip(host):
            logger.warning("Refusing cover download from non-public host: %s", url)
            return None

        try:
            # follow_redirects=False: a 3xx could otherwise bounce us to an
            # internal address that bypassed the host check above.
            with httpx.Client(follow_redirects=False, timeout=30) as client:
                with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        return None
                    cl = response.headers.get("content-length")
                    if cl and cl.isdigit() and int(cl) > _MAX_COVER_BYTES:
                        return None
                    chunks: list[bytes] = []
                    total = 0
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > _MAX_COVER_BYTES:
                            return None
                        chunks.append(chunk)
                    data = b"".join(chunks)
                suffix = self._guess_suffix(response.headers.get("content-type", ""), url)
                cover_path = self.covers_dir / f"{book_id}_cover{suffix}"
                cover_path.write_bytes(data)
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
