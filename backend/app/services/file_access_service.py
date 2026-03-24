from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.core.config import settings
from app.models.book import FileFormat


@dataclass(slots=True)
class DiscoveredFile:
    path: str
    extension: str
    file_format: str


@dataclass(slots=True)
class FileSnapshot:
    path: str
    extension: str
    file_format: str
    size: int
    mtime: datetime


class FileAccessService:
    SUPPORTED_FORMATS = {
        ".pdf": FileFormat.PDF,
        ".epub": FileFormat.EPUB,
        ".mobi": FileFormat.MOBI,
        ".azw3": FileFormat.AZW3,
        ".txt": FileFormat.TXT,
        ".djvu": FileFormat.DJVU,
    }

    def resolve_scan_root(self, requested_path: str) -> str:
        requested = Path(requested_path).resolve()
        books_dir = Path(settings.BOOKS_DIR).resolve()
        if requested != books_dir and books_dir not in requested.parents:
            raise ValueError(f"Path must be inside books directory: {books_dir}")
        if not requested.exists():
            raise ValueError(f"Path not found: {requested}")
        return str(requested)

    def resolve_book_file(self, file_path: str) -> str:
        resolved = Path(file_path).resolve()
        books_dir = Path(settings.BOOKS_DIR).resolve()
        if resolved != books_dir and books_dir not in resolved.parents:
            raise ValueError(f"Path must be inside books directory: {books_dir}")
        if not resolved.is_file():
            raise ValueError(f"File not found: {resolved}")
        return str(resolved)

    def ensure_supported_file(self, file_path: str) -> str:
        resolved = self.resolve_book_file(file_path)
        extension = Path(resolved).suffix.lower()
        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {extension}")
        return resolved

    def iter_supported_files(self, root_path: str) -> Iterable[DiscoveredFile]:
        root = Path(root_path)
        if root.is_file():
            discovered = self._to_discovered_file(root)
            if discovered:
                yield discovered
            return

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            discovered = self._to_discovered_file(path)
            if discovered:
                yield discovered

    def snapshot(self, file_path: str) -> FileSnapshot:
        resolved = Path(self.resolve_book_file(file_path))
        stat = resolved.stat()
        extension = resolved.suffix.lower()
        file_format = self.SUPPORTED_FORMATS[extension].value
        return FileSnapshot(
            path=str(resolved),
            extension=extension,
            file_format=file_format,
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime),
        )

    def guess_media_type(self, file_format: str) -> str:
        return {
            FileFormat.PDF.value: "application/pdf",
            FileFormat.EPUB.value: "application/epub+zip",
            FileFormat.MOBI.value: "application/x-mobipocket-ebook",
            FileFormat.AZW3.value: "application/vnd.amazon.ebook",
            FileFormat.TXT.value: "text/plain; charset=utf-8",
            FileFormat.DJVU.value: "image/vnd.djvu",
        }.get(file_format, "application/octet-stream")

    def _to_discovered_file(self, path: Path) -> DiscoveredFile | None:
        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_FORMATS:
            return None
        return DiscoveredFile(
            path=str(path.resolve()),
            extension=extension,
            file_format=self.SUPPORTED_FORMATS[extension].value,
        )
