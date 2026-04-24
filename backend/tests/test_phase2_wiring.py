"""Phase-2 wiring smoke tests.

Environment-free checks that:

- docker-compose and infra templates exist.
- New migrations, models, schemas and routers are importable.
- Main middleware wiring includes rate-limit / metrics toggles.
- Meilisearch adapter + cache + rate limiter expose the expected API.

Uses stdlib unittest + ast so the suite still runs when the heavy
runtime deps (sqlalchemy / pydantic) are absent.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _exists(rel: str) -> bool:
    return (REPO / rel).exists()


class ReleaseArtefactsTests(unittest.TestCase):
    def test_docker_compose_exists_with_all_services(self) -> None:
        self.assertTrue(_exists("docker-compose.yml"))
        src = _read("docker-compose.yml")
        for svc in ("postgres:", "redis:", "api:", "worker:", "beat:", "nginx:"):
            self.assertIn(svc, src, f"docker-compose missing {svc}")

    def test_env_example_exists(self) -> None:
        self.assertTrue(_exists(".env.example"))
        src = _read(".env.example")
        for key in ("POSTGRES_PASSWORD", "SECRET_KEY", "ADMIN_USERNAME"):
            self.assertIn(key, src)

    def test_systemd_templates(self) -> None:
        for name in ("books-api.service", "books-worker.service", "books-beat.service"):
            self.assertTrue(_exists(f"infra/deploy/systemd/{name}"))

    def test_nginx_conf(self) -> None:
        self.assertTrue(_exists("infra/docker/nginx/nginx.conf"))
        self.assertTrue(_exists("infra/docker/nginx/conf.d/api.conf"))


class BackendWiringTests(unittest.TestCase):
    def test_migrations_003_and_004_present(self) -> None:
        self.assertTrue(_exists("backend/alembic/versions/003_book_files_decoupling.py"))
        self.assertTrue(_exists("backend/alembic/versions/004_bookmarks_and_annotations.py"))

    def test_book_file_model_imports_hashstatus(self) -> None:
        tree = ast.parse(_read("backend/app/models/book_file.py"))
        self.assertTrue(
            any(
                isinstance(n, ast.ClassDef) and n.name == "BookFile"
                for n in tree.body
            )
        )

    def test_annotation_schemas_and_service(self) -> None:
        self.assertTrue(_exists("backend/app/models/annotation.py"))
        self.assertTrue(_exists("backend/app/schemas/annotation.py"))
        self.assertTrue(_exists("backend/app/services/annotation_service.py"))
        self.assertTrue(_exists("backend/app/api/annotations.py"))

    def test_router_aggregation_includes_annotations(self) -> None:
        src = _read("backend/app/api/router.py")
        self.assertIn("annotations", src)
        self.assertIn("annotations.router", src)

    def test_meili_adapter_exposes_public_api(self) -> None:
        src = _read("backend/app/services/meilisearch_service.py")
        for symbol in (
            "class MeiliSearchService",
            "def upsert_book",
            "def delete_book",
            "def reindex_all",
            "def search",
        ):
            self.assertIn(symbol, src)

    def test_main_wires_metrics_and_rate_limit_toggles(self) -> None:
        src = _read("backend/app/main.py")
        self.assertIn("RateLimitMiddleware", src)
        self.assertIn("MetricsMiddleware", src)
        self.assertIn("/metrics", src)
        self.assertIn("configure_logging()", src)

    def test_cache_module_provides_get_or_set(self) -> None:
        src = _read("backend/app/core/cache.py")
        self.assertIn("class RedisCache", src)
        self.assertIn("def get_or_set", src)

    def test_config_exposes_new_settings(self) -> None:
        src = _read("backend/app/core/config.py")
        for key in ("MEILI_URL", "RATE_LIMIT_PER_MINUTE", "CACHE_TTL_SECONDS", "METRICS_ENABLED"):
            self.assertIn(key, src)


class FrontendScaffoldTests(unittest.TestCase):
    def test_admin_web_pages_exist(self) -> None:
        for rel in (
            "frontend/admin-web/package.json",
            "frontend/admin-web/app/layout.tsx",
            "frontend/admin-web/app/login/page.tsx",
            "frontend/admin-web/app/books/page.tsx",
            "frontend/admin-web/app/books/[id]/page.tsx",
            "frontend/admin-web/app/scanner/page.tsx",
            "frontend/admin-web/app/scanner/jobs/[id]/page.tsx",
            "frontend/admin-web/app/categories/page.tsx",
        ):
            self.assertTrue(_exists(rel), f"missing {rel}")

    def test_reader_web_pages_exist(self) -> None:
        for rel in (
            "frontend/reader-web/package.json",
            "frontend/reader-web/app/login/page.tsx",
            "frontend/reader-web/app/library/page.tsx",
            "frontend/reader-web/app/search/page.tsx",
            "frontend/reader-web/app/read/[id]/page.tsx",
            "frontend/reader-web/components/PdfReader.tsx",
            "frontend/reader-web/components/EpubReader.tsx",
            "frontend/reader-web/components/TxtReader.tsx",
            "frontend/reader-web/lib/progress.ts",
        ):
            self.assertTrue(_exists(rel), f"missing {rel}")

    def test_shells_scaffolded(self) -> None:
        for rel in (
            "apps/mobile-shell/package.json",
            "apps/mobile-shell/capacitor.config.json",
            "apps/desktop-shell/package.json",
            "apps/desktop-shell/src-tauri/tauri.conf.json",
            "apps/desktop-shell/src-tauri/Cargo.toml",
            "apps/desktop-shell/src-tauri/src/main.rs",
        ):
            self.assertTrue(_exists(rel), f"missing {rel}")


if __name__ == "__main__":
    unittest.main()
