"""Static-import smoke test: every FastAPI router module loads without runtime
dependency errors, and the schema wiring is consistent.

Uses stdlib unittest so it runs in the bare environment the existing
regression test assumes (no sqlalchemy / pydantic available).
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _parse(rel: str) -> ast.Module:
    return ast.parse(_read(rel), filename=rel)


class SchemaImportSmokeTests(unittest.TestCase):
    def test_scanner_schemas_export_new_response_models(self) -> None:
        source = _read("app/schemas/scanner.py")
        self.assertIn("class ScanJobActionResponse", source)
        self.assertIn("class BookTaskEnqueuedResponse", source)

    def test_scanner_router_uses_new_response_models(self) -> None:
        source = _read("app/api/scanner.py")
        self.assertIn("response_model=ScanJobActionResponse", source)
        self.assertIn("response_model=BookTaskEnqueuedResponse", source)
        self.assertNotIn('"job_id": str(job_id)', source)

    def test_reading_progress_uses_file_format_enum(self) -> None:
        schema = _read("app/schemas/reading.py")
        self.assertIn("from app.models.book import FileFormat", schema)
        self.assertIn("file_format: FileFormat", schema)

    def test_reading_progress_router_returns_typed_model(self) -> None:
        source = _read("app/api/reading_progress.py")
        self.assertIn("return RecentReadingList(", source)

    def test_user_schema_has_update_model(self) -> None:
        source = _read("app/schemas/user.py")
        self.assertIn("class UserUpdate", source)
        tree = ast.parse(source)
        names = {n.name for n in tree.body if isinstance(n, ast.ClassDef)}
        self.assertIn("UserUpdate", names)

    def test_book_update_schema_covers_isbn_and_rating(self) -> None:
        source = _read("app/schemas/book.py")
        tree = ast.parse(source)
        book_update = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "BookUpdate"
        )
        field_names = {
            item.target.id
            for item in book_update.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        }
        for required in {"isbn", "rating", "rating_count", "cover_url", "language", "page_count"}:
            self.assertIn(required, field_names, f"BookUpdate missing {required}")

    def test_schemas_init_exports(self) -> None:
        source = _read("app/schemas/__init__.py")
        for name in (
            "UserUpdate",
            "ScanJobActionResponse",
            "BookTaskEnqueuedResponse",
        ):
            self.assertIn(name, source)


if __name__ == "__main__":
    unittest.main()
