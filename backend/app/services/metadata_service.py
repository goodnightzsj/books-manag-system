import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.models.book import Book
from app.services.search_service import BookSearchService

logger = logging.getLogger(__name__)


class MetadataExtractor:
    def extract(self, file_path: str, file_ext: str) -> dict[str, Any]:
        if file_ext == ".pdf":
            return self._extract_pdf(file_path)
        if file_ext == ".epub":
            return self._extract_epub(file_path)
        if file_ext == ".mobi":
            return self._extract_mobi(file_path)
        if file_ext == ".txt":
            return self._extract_txt(file_path)
        return self._extract_basic(file_path)

    def _extract_pdf(self, file_path: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        try:
            import PyPDF2

            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    metadata["title"] = info.get("/Title", "")
                    metadata["author"] = info.get("/Author", "")
                    metadata["subject"] = info.get("/Subject", "")
                metadata["page_count"] = len(pdf_reader.pages)
        except Exception as exc:
            logger.error("Error extracting PDF metadata from %s: %s", file_path, exc)
            metadata = self._extract_basic(file_path)
        return metadata

    def _extract_epub(self, file_path: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        try:
            import ebookmeta

            epub = ebookmeta.get_metadata(file_path)
            if epub:
                metadata["title"] = epub.title or ""
                metadata["author"] = ", ".join(epub.author_list) if epub.author_list else ""
                metadata["description"] = epub.description or ""
                metadata["publisher"] = epub.publisher or ""
                metadata["isbn"] = epub.isbn or ""
                metadata["language"] = epub.language or "zh"
        except Exception as exc:
            logger.error("Error extracting EPUB metadata from %s: %s", file_path, exc)
            metadata = self._extract_basic(file_path)
        return metadata

    def _extract_mobi(self, file_path: str) -> dict[str, Any]:
        return self._extract_basic(file_path)

    def _extract_txt(self, file_path: str) -> dict[str, Any]:
        metadata = self._extract_basic(file_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                first_lines: list[str] = []
                for index, line in enumerate(file):
                    if index >= 5:
                        break
                    if line.strip():
                        first_lines.append(line.strip())
                if first_lines:
                    metadata["description"] = " ".join(first_lines)[:200] + "..."
        except Exception as exc:
            logger.error("Error reading TXT file %s: %s", file_path, exc)
        return metadata

    def _extract_basic(self, file_path: str) -> dict[str, Any]:
        file_name = Path(file_path).stem
        title = file_name
        author = None

        if "《" in file_name and "》" in file_name:
            start = file_name.index("《")
            end = file_name.index("》")
            title = file_name[start + 1 : end]
            remaining = file_name[end + 1 :].strip()
            if remaining:
                author = remaining
        elif "-" in file_name:
            parts = file_name.split("-", 1)
            if len(parts) == 2:
                title = parts[0].strip()
                author = parts[1].strip()

        return {
            "title": title,
            "author": author,
            "language": "zh",
        }


class OnlineMetadataService:
    def __init__(self, douban_api_url: str = "https://douban.uieee.com"):
        self.douban_api_url = douban_api_url

    def fetch_best_match(
        self,
        *,
        isbn: str | None,
        title: str | None,
        api_key: str | None = None,
    ) -> tuple[str | None, dict[str, Any] | None]:
        if isbn:
            metadata = self.fetch_from_douban(isbn=isbn)
            if metadata:
                return "douban", metadata

        if title:
            metadata = self.fetch_from_douban(title=title)
            if metadata:
                return "douban", metadata

        if isbn:
            metadata = self.fetch_from_google_books(isbn=isbn, api_key=api_key)
            if metadata:
                return "google_books", metadata

        return None, None

    def fetch_from_douban(self, isbn: str | None = None, title: str | None = None) -> dict[str, Any] | None:
        if not isbn and not title:
            return None

        try:
            with httpx.Client() as client:
                if isbn:
                    url = f"{self.douban_api_url}/v2/book/isbn/{isbn}"
                    response = client.get(url, timeout=10)
                else:
                    url = f"{self.douban_api_url}/v2/book/search"
                    response = client.get(url, params={"q": title}, timeout=10)

                if response.status_code == 200:
                    return self._parse_douban_response(response.json())
        except Exception as exc:
            logger.error("Error fetching from Douban: %s", exc)

        return None

    def _parse_douban_response(self, data: dict[str, Any]) -> dict[str, Any]:
        if "books" in data and data["books"]:
            book = data["books"][0]
        else:
            book = data

        return {
            "title": book.get("title"),
            "subtitle": book.get("subtitle"),
            "author": ", ".join(book.get("author", [])),
            "publisher": book.get("publisher"),
            "publish_date": book.get("pubdate"),
            "isbn": book.get("isbn13") or book.get("isbn10"),
            "description": book.get("summary"),
            "cover_url": book.get("image") or book.get("images", {}).get("large"),
            "rating": book.get("rating", {}).get("average"),
            "rating_count": book.get("rating", {}).get("numRaters"),
            "tags": [tag.get("name") for tag in book.get("tags", [])],
        }

    def fetch_from_google_books(
        self,
        isbn: str | None = None,
        title: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any] | None:
        if not isbn and not title:
            return None

        try:
            with httpx.Client() as client:
                params: dict[str, str] = {}
                if api_key:
                    params["key"] = api_key
                params["q"] = f"isbn:{isbn}" if isbn else (title or "")
                response = client.get("https://www.googleapis.com/books/v1/volumes", params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("totalItems", 0) > 0:
                        return self._parse_google_books_response(data["items"][0])
        except Exception as exc:
            logger.error("Error fetching from Google Books: %s", exc)

        return None

    def _parse_google_books_response(self, item: dict[str, Any]) -> dict[str, Any]:
        volume_info = item.get("volumeInfo", {})
        identifiers = volume_info.get("industryIdentifiers", [])
        isbn = next(
            (
                identifier["identifier"]
                for identifier in identifiers
                if identifier["type"] in {"ISBN_13", "ISBN_10"}
            ),
            None,
        )

        return {
            "title": volume_info.get("title"),
            "subtitle": volume_info.get("subtitle"),
            "author": ", ".join(volume_info.get("authors", [])),
            "publisher": volume_info.get("publisher"),
            "publish_date": volume_info.get("publishedDate"),
            "isbn": isbn,
            "description": volume_info.get("description"),
            "cover_url": volume_info.get("imageLinks", {}).get("thumbnail"),
            "page_count": volume_info.get("pageCount"),
            "language": volume_info.get("language"),
            "categories": volume_info.get("categories", []),
        }


@dataclass(slots=True)
class MetadataSyncResult:
    book_id: UUID
    provider: str | None
    updated_fields: list[str]
    cover_source_url: str | None
    found: bool


class MetadataSyncService:
    FIELD_MAP = {
        "title": "title",
        "subtitle": "subtitle",
        "author": "author",
        "publisher": "publisher",
        "description": "description",
        "isbn": "isbn",
        "language": "language",
        "page_count": "page_count",
        "rating": "rating",
        "rating_count": "rating_count",
        "tags": "tags",
    }

    def __init__(
        self,
        db: Session,
        online_service: OnlineMetadataService | None = None,
        google_api_key: str | None = None,
    ):
        self.db = db
        self.online_service = online_service or OnlineMetadataService()
        self.google_api_key = google_api_key

    def sync_book(self, book_id: UUID, *, force: bool = False) -> MetadataSyncResult | None:
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None

        provider, metadata = self.online_service.fetch_best_match(
            isbn=book.isbn,
            title=book.title,
            api_key=self.google_api_key,
        )
        if not metadata:
            return MetadataSyncResult(
                book_id=book.id,
                provider=None,
                updated_fields=[],
                cover_source_url=None,
                found=False,
            )

        updated_fields: list[str] = []
        for metadata_field, book_attr in self.FIELD_MAP.items():
            value = metadata.get(metadata_field)
            if not self._has_value(value):
                continue

            normalized_value = self._normalize_value(book_attr, value)
            current_value = getattr(book, book_attr)
            if not force and self._has_value(current_value):
                continue
            if current_value == normalized_value:
                continue

            setattr(book, book_attr, normalized_value)
            updated_fields.append(book_attr)

        merged_metadata = dict(book.book_metadata or {})
        for key, value in metadata.items():
            if self._has_value(value):
                merged_metadata[key] = value
        book.book_metadata = merged_metadata
        book.source_provider = provider
        book.metadata_synced_at = datetime.utcnow()
        BookSearchService(self.db).refresh_document(book.id)

        cover_source_url = metadata.get("cover_url") if self._has_value(metadata.get("cover_url")) else None
        return MetadataSyncResult(
            book_id=book.id,
            provider=provider,
            updated_fields=updated_fields,
            cover_source_url=cover_source_url,
            found=True,
        )

    def _normalize_value(self, field_name: str, value: Any) -> Any:
        if field_name == "rating":
            return float(value)
        if field_name in {"rating_count", "page_count"}:
            return int(value)
        if field_name == "tags":
            return list(value) if isinstance(value, list) else [str(value)]
        if isinstance(value, str):
            return value.strip()
        return value

    def _has_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return True
