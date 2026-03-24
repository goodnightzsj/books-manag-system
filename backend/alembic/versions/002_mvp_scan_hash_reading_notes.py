"""mvp scan/hash/reading/notes

Revision ID: 002
Revises: 001
Create Date: 2026-03-24 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    hash_status_enum = sa.Enum("pending", "done", "failed", "skipped", name="hashstatus")
    scan_job_type_enum = sa.Enum("scan_directory", "scan_file", "rehash", "resync_metadata", name="scanjobtype")
    scan_job_status_enum = sa.Enum("queued", "running", "completed", "failed", "partial_success", "cancelled", name="scanjobstatus")
    scan_item_status_enum = sa.Enum("queued", "processing", "created", "updated", "skipped", "failed", name="scanitemstatus")

    bind = op.get_bind()
    hash_status_enum.create(bind, checkfirst=True)
    scan_job_type_enum.create(bind, checkfirst=True)
    scan_job_status_enum.create(bind, checkfirst=True)
    scan_item_status_enum.create(bind, checkfirst=True)

    op.add_column("books", sa.Column("content_hash", sa.String(length=128), nullable=True))
    op.add_column("books", sa.Column("hash_algorithm", sa.String(length=32), nullable=True))
    op.add_column("books", sa.Column("hash_status", hash_status_enum, nullable=False, server_default="pending"))
    op.add_column("books", sa.Column("hash_error", sa.Text(), nullable=True))
    op.add_column("books", sa.Column("file_mtime", sa.DateTime(), nullable=True))
    op.add_column("books", sa.Column("source_provider", sa.String(length=32), nullable=True))
    op.add_column("books", sa.Column("metadata_synced_at", sa.DateTime(), nullable=True))
    op.add_column("books", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))
    op.alter_column("books", "hash_status", server_default=None)

    op.create_index("ix_books_content_hash", "books", ["content_hash"], unique=False)
    op.create_index("ix_books_file_path", "books", ["file_path"], unique=True)
    op.create_index("ix_books_search_vector", "books", ["search_vector"], unique=False, postgresql_using="gin")
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_title_trgm ON books USING gin (title gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_author_trgm ON books USING gin (author gin_trgm_ops)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_books_content_hash_not_null ON books (content_hash) WHERE content_hash IS NOT NULL")

    op.create_table(
        "scan_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", scan_job_type_enum, nullable=False),
        sa.Column("status", scan_job_status_enum, nullable=False, server_default="queued"),
        sa.Column("requested_path", sa.Text(), nullable=False),
        sa.Column("normalized_path", sa.Text(), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_jobs_status_created_at", "scan_jobs", ["status", "created_at"], unique=False)
    op.create_index("ix_scan_jobs_created_by", "scan_jobs", ["created_by"], unique=False)

    op.create_table(
        "scan_job_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_format", sa.String(length=16), nullable=True),
        sa.Column("status", scan_item_status_enum, nullable=False, server_default="queued"),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detected_hash", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["scan_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_job_items_job_id", "scan_job_items", ["job_id"], unique=False)
    op.create_index("ix_scan_job_items_job_id_status", "scan_job_items", ["job_id", "status"], unique=False)

    op.add_column("reading_progress", sa.Column("locator", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_unique_constraint("uq_reading_progress_user_book", "reading_progress", ["user_id", "book_id"])

    op.create_table(
        "book_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("locator", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_book_notes_user_book", "book_notes", ["user_id", "book_id", "updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_book_notes_user_book", table_name="book_notes")
    op.drop_table("book_notes")

    op.drop_constraint("uq_reading_progress_user_book", "reading_progress", type_="unique")
    op.drop_column("reading_progress", "locator")

    op.drop_index("ix_scan_job_items_job_id_status", table_name="scan_job_items")
    op.drop_index("ix_scan_job_items_job_id", table_name="scan_job_items")
    op.drop_table("scan_job_items")

    op.drop_index("ix_scan_jobs_created_by", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_status_created_at", table_name="scan_jobs")
    op.drop_table("scan_jobs")

    op.execute("DROP INDEX IF EXISTS uq_books_content_hash_not_null")
    op.execute("DROP INDEX IF EXISTS ix_books_author_trgm")
    op.execute("DROP INDEX IF EXISTS ix_books_title_trgm")
    op.drop_index("ix_books_search_vector", table_name="books")
    op.drop_index("ix_books_file_path", table_name="books")
    op.drop_index("ix_books_content_hash", table_name="books")

    op.drop_column("books", "search_vector")
    op.drop_column("books", "metadata_synced_at")
    op.drop_column("books", "source_provider")
    op.drop_column("books", "file_mtime")
    op.drop_column("books", "hash_error")
    op.drop_column("books", "hash_status")
    op.drop_column("books", "hash_algorithm")
    op.drop_column("books", "content_hash")

    op.execute("DROP TYPE IF EXISTS scanitemstatus")
    op.execute("DROP TYPE IF EXISTS scanjobstatus")
    op.execute("DROP TYPE IF EXISTS scanjobtype")
    op.execute("DROP TYPE IF EXISTS hashstatus")
