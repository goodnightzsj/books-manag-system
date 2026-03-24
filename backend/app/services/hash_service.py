import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.models.book import Book, HashStatus


@dataclass(slots=True)
class HashDecision:
    should_hash: bool
    next_status: HashStatus
    reason: str


class HashService:
    DEFAULT_ALGORITHM = "sha256"
    CHUNK_SIZE = 1024 * 1024

    def should_hash(
        self,
        book: Book | None,
        *,
        file_path: str,
        file_size: int,
        file_mtime: datetime,
    ) -> HashDecision:
        if book is None:
            return HashDecision(True, HashStatus.PENDING, "new_book")

        same_snapshot = (
            book.file_path == file_path
            and book.file_size == file_size
            and self._same_mtime(book.file_mtime, file_mtime)
        )
        has_current_hash = (
            bool(book.content_hash)
            and book.hash_algorithm == self.DEFAULT_ALGORITHM
            and book.hash_status in {HashStatus.DONE, HashStatus.SKIPPED}
        )

        if same_snapshot and has_current_hash:
            return HashDecision(False, HashStatus.SKIPPED, "unchanged_snapshot")

        return HashDecision(True, HashStatus.PENDING, "rehash_required")

    def compute_sha256(self, file_path: str) -> str:
        digest = hashlib.sha256()
        with Path(file_path).open("rb") as file:
            while chunk := file.read(self.CHUNK_SIZE):
                digest.update(chunk)
        return digest.hexdigest()

    def classify_error(self, exc: Exception) -> str:
        if isinstance(exc, FileNotFoundError):
            return f"file_not_found: {exc}"
        if isinstance(exc, PermissionError):
            return f"permission_denied: {exc}"
        if isinstance(exc, OSError):
            return f"io_error: {exc}"
        return f"unexpected_error: {exc}"

    def _same_mtime(self, left: datetime | None, right: datetime | None, *, tolerance_seconds: float = 1.0) -> bool:
        if left is None or right is None:
            return False
        return abs((left - right).total_seconds()) <= tolerance_seconds
