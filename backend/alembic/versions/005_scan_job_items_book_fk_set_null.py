"""scan_job_items.book_id FK -> ON DELETE SET NULL

Deleting a book used to fail with a ForeignKeyViolation because
scan_job_items referenced it with a plain (NO ACTION) FK. A scan-job item is
an audit record of what was scanned, so we keep the row but unlink it.

Revision ID: 005
Revises: 004
Create Date: 2026-05-12 04:10:00.000000
"""
from alembic import op


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


# Postgres auto-generates the constraint name as "<table>_<col>_fkey".
_FK_NAME = "scan_job_items_book_id_fkey"


def upgrade():
    op.drop_constraint(_FK_NAME, "scan_job_items", type_="foreignkey")
    op.create_foreign_key(
        _FK_NAME,
        "scan_job_items",
        "books",
        ["book_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(_FK_NAME, "scan_job_items", type_="foreignkey")
    op.create_foreign_key(
        _FK_NAME,
        "scan_job_items",
        "books",
        ["book_id"],
        ["id"],
    )
