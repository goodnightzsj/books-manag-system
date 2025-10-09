"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
    sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create categories table
    op.create_table('categories',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)

    # Create books table
    op.create_table('books',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('subtitle', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('publish_date', sa.DateTime(), nullable=True),
    sa.Column('isbn', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('cover_url', sa.String(), nullable=True),
    sa.Column('file_path', sa.String(), nullable=False),
    sa.Column('file_format', sa.Enum('PDF', 'EPUB', 'MOBI', 'AZW3', 'TXT', 'DJVU', name='fileformat'), nullable=False),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('language', sa.String(), nullable=True),
    sa.Column('page_count', sa.Integer(), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('rating_count', sa.Integer(), nullable=True),
    sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('book_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('indexed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_author'), 'books', ['author'], unique=False)
    op.create_index(op.f('ix_books_isbn'), 'books', ['isbn'], unique=True)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)

    # Create book_categories association table
    op.create_table('book_categories',
    sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('book_id', 'category_id')
    )

    # Create reading_progress table
    op.create_table('reading_progress',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('current_page', sa.Integer(), nullable=True),
    sa.Column('total_pages', sa.Integer(), nullable=True),
    sa.Column('progress_percent', sa.Float(), nullable=True),
    sa.Column('status', sa.Enum('not_started', 'reading', 'completed', 'abandoned', name='readingstatus'), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('last_read_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('bookmarks', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('reading_progress')
    op.drop_table('book_categories')
    op.drop_index(op.f('ix_books_title'), table_name='books')
    op.drop_index(op.f('ix_books_isbn'), table_name='books')
    op.drop_index(op.f('ix_books_author'), table_name='books')
    op.drop_table('books')
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_table('categories')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS fileformat')
    op.execute('DROP TYPE IF EXISTS readingstatus')
