from sqlalchemy.orm import Session

from app.services.book_ingest_service import BookIngestService, BookUpsertResult
from app.services.file_access_service import FileAccessService
from app.services.metadata_service import MetadataExtractor


class ScanService:
    def __init__(
        self,
        db: Session,
        file_access: FileAccessService | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        book_ingest: BookIngestService | None = None,
    ):
        self.db = db
        self.file_access = file_access or FileAccessService()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.book_ingest = book_ingest or BookIngestService(db)

    def process_file(self, file_path: str) -> BookUpsertResult:
        snapshot = self.file_access.snapshot(file_path)
        metadata = self.metadata_extractor.extract(snapshot.path, snapshot.extension)
        try:
            result = self.book_ingest.upsert_scanned_book(
                file_path=snapshot.path,
                file_format=snapshot.file_format,
                file_size=snapshot.size,
                file_mtime=snapshot.mtime,
                metadata=metadata,
            )
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise
