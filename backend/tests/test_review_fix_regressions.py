import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SourceFileTestCase(unittest.TestCase):
    def parse_module(self, relative_path: str) -> ast.Module:
        return ast.parse(self.read_text(relative_path))

    def read_text(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def get_function(self, module: ast.Module, name: str) -> ast.FunctionDef:
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        self.fail(f"Function {name} not found")

    def get_class(self, module: ast.Module, name: str) -> ast.ClassDef:
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == name:
                return node
        self.fail(f"Class {name} not found")

    def get_method(self, class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        self.fail(f"Method {name} not found in class {class_node.name}")


class BooksApiRegressionTests(SourceFileTestCase):
    def test_books_unique_conflicts_are_mapped_to_http_409(self) -> None:
        module = self.parse_module("backend/app/api/books.py")

        helper = self.get_function(module, "_raise_integrity_error")
        helper_source = ast.unparse(helper)
        self.assertIn("HTTP_409_CONFLICT", helper_source)
        self.assertIn("file_path", helper_source)
        self.assertIn("isbn", helper_source)

        for function_name in ("create_book", "update_book"):
            function_node = self.get_function(module, function_name)
            try_nodes = [node for node in ast.walk(function_node) if isinstance(node, ast.Try)]
            self.assertTrue(try_nodes, f"{function_name} should catch IntegrityError")
            matching_handler = None
            for try_node in try_nodes:
                for handler in try_node.handlers:
                    if isinstance(handler.type, ast.Name) and handler.type.id == "IntegrityError":
                        matching_handler = handler
                        break
                if matching_handler:
                    break
            self.assertIsNotNone(matching_handler, f"{function_name} should handle IntegrityError")
            handler_source = ast.unparse(matching_handler)
            self.assertIn("db.rollback()", handler_source)
            self.assertIn("_raise_integrity_error(exc)", handler_source)


class ReadingSchemaRegressionTests(SourceFileTestCase):
    def test_reading_progress_update_no_longer_exposes_legacy_fields(self) -> None:
        module = self.parse_module("backend/app/schemas/reading.py")
        reading_progress_update = self.get_class(module, "ReadingProgressUpdate")
        field_names = {
            target.id
            for node in reading_progress_update.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
            for target in [node.target]
        }

        self.assertNotIn("notes", field_names)
        self.assertNotIn("bookmarks", field_names)
        self.assertTrue({"current_page", "progress_percent", "status", "locator"}.issubset(field_names))

    def test_reading_service_upsert_no_longer_writes_legacy_fields(self) -> None:
        module = self.parse_module("backend/app/services/reading_service.py")
        service_class = self.get_class(module, "ReadingProgressService")
        upsert_for_user = self.get_method(service_class, "upsert_for_user")
        upsert_source = ast.unparse(upsert_for_user)

        self.assertNotIn("'notes'", upsert_source)
        self.assertNotIn("'bookmarks'", upsert_source)
        self.assertIn("'current_page'", upsert_source)
        self.assertIn("'finished_at'", upsert_source)


class BookIngestRegressionTests(SourceFileTestCase):
    def test_mergeable_fields_are_centralized_on_service_class(self) -> None:
        module = self.parse_module("backend/app/services/book_ingest_service.py")
        service_class = self.get_class(module, "BookIngestService")

        mergeable_fields_node = None
        merge_book_fields_node = None
        for node in service_class.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "MERGEABLE_BOOK_FIELDS" for target in node.targets):
                mergeable_fields_node = node
            if isinstance(node, ast.FunctionDef) and node.name == "_merge_book_fields":
                merge_book_fields_node = node

        self.assertIsNotNone(mergeable_fields_node, "MERGEABLE_BOOK_FIELDS should exist")
        self.assertIsNotNone(merge_book_fields_node, "_merge_book_fields should exist")

        field_names = [elt.value for elt in mergeable_fields_node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
        self.assertIn("isbn", field_names)
        self.assertIn("book_metadata", field_names)
        self.assertIn("metadata_synced_at", field_names)

        merge_source = ast.unparse(merge_book_fields_node)
        self.assertIn("self.MERGEABLE_BOOK_FIELDS", merge_source)


class ScanJobServiceRegressionTests(SourceFileTestCase):
    def test_retry_failed_items_returns_early_when_no_failed_rows(self) -> None:
        module = self.parse_module("backend/app/services/scan_job_service.py")
        service_class = self.get_class(module, "ScanJobService")
        retry_failed_items = self.get_method(service_class, "retry_failed_items")

        first_if = next((node for node in retry_failed_items.body if isinstance(node, ast.If)), None)
        self.assertIsNotNone(first_if, "retry_failed_items should guard empty failed item set")
        self.assertEqual(ast.unparse(first_if.test), "not items")
        self.assertEqual(len(first_if.body), 1)
        self.assertIsInstance(first_if.body[0], ast.Return)
        self.assertEqual(ast.literal_eval(first_if.body[0].value), 0)

        function_source = ast.unparse(retry_failed_items)
        self.assertIn("job.status = ScanJobStatus.RUNNING", function_source)
        self.assertIn("job.finished_at = None", function_source)
        self.assertIn("job.error_message = None", function_source)


if __name__ == "__main__":
    unittest.main()
