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
    hash_status_enum = sa.Enum(
        "pending", "done", "failed", "skipped", name="hashstatus", create_type=False
    )

    op.create_table(
        "book_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_format", sa.String(length=16), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("file_mtime", sa.DateTime(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("hash_algorithm", sa.String(length=32), nullable=True),
        sa.Column("hash_status", hash_status_enum, nullable=False, server_default="pending"),
        sa.Column("hash_error", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("indexed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
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
