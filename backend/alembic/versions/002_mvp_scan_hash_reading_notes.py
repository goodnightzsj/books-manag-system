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

    # Create the four enum types idempotently. Wrapping each in a DO block
    # with EXCEPTION duplicate_object means partial-failure reruns work and
    # there is exactly one creation point, after which all column references
    # use postgresql.ENUM(..., create_type=False) so SQLAlchemy never tries
    # to re-emit CREATE TYPE.
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE hashstatus AS ENUM ('pending', 'done', 'failed', 'skipped');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
        CREATE TYPE scanjobtype AS ENUM ('scan_directory', 'scan_file', 'rehash', 'resync_metadata');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
        CREATE TYPE scanjobstatus AS ENUM ('queued', 'running', 'completed', 'failed', 'partial_success', 'cancelled');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
        CREATE TYPE scanitemstatus AS ENUM ('queued', 'processing', 'created', 'updated', 'skipped', 'failed');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Use raw SQL for column / table creation that involves the enum types.
    # SQLAlchemy 2.0 / alembic still emits CREATE TYPE for postgresql.ENUM
    # references even with create_type=False in some pathways, so this
    # bypass keeps the migration deterministic.
    op.execute("ALTER TABLE books ADD COLUMN content_hash VARCHAR(128)")
    op.execute("ALTER TABLE books ADD COLUMN hash_algorithm VARCHAR(32)")
    op.execute("ALTER TABLE books ADD COLUMN hash_status hashstatus NOT NULL DEFAULT 'pending'")
    op.execute("ALTER TABLE books ALTER COLUMN hash_status DROP DEFAULT")
    op.execute("ALTER TABLE books ADD COLUMN hash_error TEXT")
    op.execute("ALTER TABLE books ADD COLUMN file_mtime TIMESTAMP")
    op.execute("ALTER TABLE books ADD COLUMN source_provider VARCHAR(32)")
    op.execute("ALTER TABLE books ADD COLUMN metadata_synced_at TIMESTAMP")
    op.execute("ALTER TABLE books ADD COLUMN search_vector TSVECTOR")

    op.create_index("ix_books_content_hash", "books", ["content_hash"], unique=False)
    op.create_index("ix_books_file_path", "books", ["file_path"], unique=True)
    op.create_index("ix_books_search_vector", "books", ["search_vector"], unique=False, postgresql_using="gin")
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_title_trgm ON books USING gin (title gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_author_trgm ON books USING gin (author gin_trgm_ops)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_books_content_hash_not_null ON books (content_hash) WHERE content_hash IS NOT NULL")

    op.execute("""
        CREATE TABLE scan_jobs (
            id              UUID PRIMARY KEY,
            job_type        scanjobtype   NOT NULL,
            status          scanjobstatus NOT NULL DEFAULT 'queued',
            requested_path  TEXT          NOT NULL,
            normalized_path TEXT          NOT NULL,
            total_items     INTEGER       NOT NULL DEFAULT 0,
            processed_items INTEGER       NOT NULL DEFAULT 0,
            success_items   INTEGER       NOT NULL DEFAULT 0,
            failed_items    INTEGER       NOT NULL DEFAULT 0,
            skipped_items   INTEGER       NOT NULL DEFAULT 0,
            error_message   TEXT,
            created_by      UUID REFERENCES users(id),
            created_at      TIMESTAMP NOT NULL,
            started_at      TIMESTAMP,
            finished_at     TIMESTAMP
        )
    """)
    op.create_index("ix_scan_jobs_status_created_at", "scan_jobs", ["status", "created_at"], unique=False)
    op.create_index("ix_scan_jobs_created_by", "scan_jobs", ["created_by"], unique=False)

    op.execute("""
        CREATE TABLE scan_job_items (
            id            UUID PRIMARY KEY,
            job_id        UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
            file_path     TEXT NOT NULL,
            file_format   VARCHAR(16),
            status        scanitemstatus NOT NULL DEFAULT 'queued',
            book_id       UUID REFERENCES books(id),
            detected_hash VARCHAR(128),
            error_message TEXT,
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL
        )
    """)
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
