"""book_files decoupling

Revision ID: 003
Revises: 002
Create Date: 2026-04-25 00:00:00.000000

Additive migration: introduces `book_files` for multi-copy support while
keeping the legacy columns on `books` intact for backward compatibility.
Back-fills one `book_files` row per existing `books` row.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # Raw SQL to avoid SA emitting CREATE TYPE for the existing `hashstatus`
    # enum (idempotently created by migration 002).
    op.execute("""
        CREATE TABLE book_files (
            id              UUID PRIMARY KEY,
            book_id         UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            file_path       TEXT NOT NULL,
            file_format     VARCHAR(16) NOT NULL,
            file_size       BIGINT,
            file_mtime      TIMESTAMP,
            content_hash    VARCHAR(128),
            hash_algorithm  VARCHAR(32),
            hash_status     hashstatus NOT NULL DEFAULT 'pending',
            hash_error      TEXT,
            is_primary      BOOLEAN NOT NULL DEFAULT TRUE,
            indexed_at      TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)
    op.create_index("ix_book_files_book_id", "book_files", ["book_id"], unique=False)
    op.create_index("ix_book_files_file_path", "book_files", ["file_path"], unique=True)
    op.create_index("ix_book_files_content_hash", "book_files", ["content_hash"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_book_files_content_hash_not_null "
        "ON book_files (content_hash) WHERE content_hash IS NOT NULL"
    )

    # Back-fill: one row per existing book.
    op.execute(
        """
        INSERT INTO book_files (
            id, book_id, file_path, file_format, file_size, file_mtime,
            content_hash, hash_algorithm, hash_status, hash_error,
            is_primary, indexed_at, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            id,
            file_path,
            file_format::text,
            file_size,
            file_mtime,
            content_hash,
            hash_algorithm,
            hash_status,
            hash_error,
            true,
            indexed_at,
            COALESCE(created_at, NOW()),
            COALESCE(updated_at, NOW())
        FROM books
        WHERE NOT EXISTS (SELECT 1 FROM book_files bf WHERE bf.book_id = books.id)
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_book_files_content_hash_not_null")
    op.drop_index("ix_book_files_content_hash", table_name="book_files")
    op.drop_index("ix_book_files_file_path", table_name="book_files")
    op.drop_index("ix_book_files_book_id", table_name="book_files")
    op.drop_table("book_files")
