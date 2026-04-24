"""Meilisearch adapter.

Phase-2 search backend. Activates when ``settings.MEILI_URL`` is set.
PostgreSQL remains the source of truth; this adapter mirrors a subset
of book fields for faster, more forgiving full-text search.

API surface:

- ``MeiliSearchService.is_enabled`` -- env-flag check.
- ``upsert_book(book)`` / ``delete_book(book_id)`` -- sync a single row.
- ``reindex_all(books)`` -- bulk bootstrap.
- ``search(q, filters=...)`` -- returns ``[{id, _score?}, ...]``.

Network errors are swallowed and logged; PG FTS is the fallback so a
Meilisearch outage must not break the catalogue API.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Optional
from uuid import UUID

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

INDEX_NAME = "books"
PRIMARY_KEY = "id"
SEARCHABLE_ATTRS = ["title", "author", "publisher", "isbn", "description", "tags"]
FILTERABLE_ATTRS = ["file_format", "hash_status", "language", "tags"]
SORTABLE_ATTRS = ["rating", "rating_count", "created_at", "updated_at"]


def _to_document(book: Any) -> dict[str, Any]:
    """Convert a Book ORM row (or a dict) to a Meili document."""
    get = (lambda k: book.get(k)) if isinstance(book, dict) else (lambda k: getattr(book, k, None))
    file_format = get("file_format")
    fmt_value = getattr(file_format, "value", file_format)
    hash_status = get("hash_status")
    hs_value = getattr(hash_status, "value", hash_status)
    return {
        "id": str(get("id")),
        "title": get("title") or "",
        "author": get("author") or "",
        "publisher": get("publisher") or "",
        "isbn": get("isbn") or "",
        "description": get("description") or "",
        "language": get("language") or "",
        "tags": get("tags") or [],
        "file_format": fmt_value,
        "hash_status": hs_value,
        "rating": get("rating"),
        "rating_count": get("rating_count"),
        "cover_url": get("cover_url"),
        "created_at": _ts(get("created_at")),
        "updated_at": _ts(get("updated_at")),
    }


def _ts(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class MeiliSearchService:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        self.url = (url or getattr(settings, "MEILI_URL", "") or "").rstrip("/")
        self.api_key = api_key or getattr(settings, "MEILI_MASTER_KEY", "") or ""
        self.timeout = timeout

    @property
    def is_enabled(self) -> bool:
        return bool(self.url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ----- admin operations -----
    def ensure_index(self) -> None:
        if not self.is_enabled:
            return
        with httpx.Client(timeout=self.timeout) as client:
            try:
                client.post(
                    f"{self.url}/indexes",
                    json={"uid": INDEX_NAME, "primaryKey": PRIMARY_KEY},
                    headers=self._headers(),
                )
                client.patch(
                    f"{self.url}/indexes/{INDEX_NAME}/settings/searchable-attributes",
                    json=SEARCHABLE_ATTRS,
                    headers=self._headers(),
                )
                client.patch(
                    f"{self.url}/indexes/{INDEX_NAME}/settings/filterable-attributes",
                    json=FILTERABLE_ATTRS,
                    headers=self._headers(),
                )
                client.patch(
                    f"{self.url}/indexes/{INDEX_NAME}/settings/sortable-attributes",
                    json=SORTABLE_ATTRS,
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                logger.warning("meili ensure_index failed: %s", exc)

    def upsert_book(self, book: Any) -> None:
        if not self.is_enabled:
            return
        self._post_documents([_to_document(book)])

    def upsert_bulk(self, books: Iterable[Any]) -> None:
        if not self.is_enabled:
            return
        docs = [_to_document(b) for b in books]
        if docs:
            self._post_documents(docs)

    def delete_book(self, book_id: UUID) -> None:
        if not self.is_enabled:
            return
        with httpx.Client(timeout=self.timeout) as client:
            try:
                client.delete(
                    f"{self.url}/indexes/{INDEX_NAME}/documents/{book_id}",
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                logger.warning("meili delete_book failed: %s", exc)

    def reindex_all(self, books: Iterable[Any]) -> None:
        if not self.is_enabled:
            return
        self.ensure_index()
        self.upsert_bulk(books)

    # ----- query -----
    def search(
        self,
        q: str,
        *,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[list[str]] = None,
        sort: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        if not self.is_enabled:
            return []
        body: dict[str, Any] = {"q": q, "limit": limit, "offset": offset}
        if filters:
            body["filter"] = filters
        if sort:
            body["sort"] = sort
        with httpx.Client(timeout=self.timeout) as client:
            try:
                r = client.post(
                    f"{self.url}/indexes/{INDEX_NAME}/search",
                    json=body,
                    headers=self._headers(),
                )
                r.raise_for_status()
                data = r.json()
                return data.get("hits", [])
            except httpx.HTTPError as exc:
                logger.warning("meili search failed, falling back: %s", exc)
                return []

    # ----- internals -----
    def _post_documents(self, docs: list[dict[str, Any]]) -> None:
        with httpx.Client(timeout=self.timeout) as client:
            try:
                r = client.post(
                    f"{self.url}/indexes/{INDEX_NAME}/documents",
                    json=docs,
                    headers=self._headers(),
                )
                r.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("meili upsert failed: %s", exc)
