# Books Platform MVP - Alembic Migration Draft + Pydantic Schema Draft

## 0. 目标

基于当前代码基线，产出 **MVP 级别** 的：
1. Alembic 迁移草案
2. Pydantic schema 设计稿

约束：
- 不推翻现有 `books` 模型
- 不在 MVP 就引入 `book_files`
- 以最小改动支持：hash 入库、扫描任务、阅读进度、基础笔记、搜索升级

当前参考：
- 迁移基线：`backend/alembic/versions/001_initial.py:19-126`
- Book schema：`backend/app/schemas/book.py:6-46`
- User schema：`backend/app/schemas/user.py:7-32`
- Category schema：`backend/app/schemas/category.py:6-19`
- Schema exports：`backend/app/schemas/__init__.py:1-9`

---

# 1. Alembic 迁移草案

## 1.1 建议迁移文件名

建议新增一个迁移，例如：
- `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py`

---

## 1.2 迁移目标

本迁移完成以下事情：

### A. `books` 表增强
新增字段：
- `content_hash`
- `hash_algorithm`
- `hash_status`
- `hash_error`
- `file_mtime`
- `source_provider`
- `metadata_synced_at`
- `search_vector`

新增索引：
- `books_content_hash_idx`
- `books_file_path_idx`
- `books_search_vector_idx`
- trigram index for title
- trigram index for author

新增约束：
- `UNIQUE (content_hash) WHERE content_hash IS NOT NULL`

### B. `scan_jobs` 表
新增任务主表

### C. `scan_job_items` 表
新增任务明细表

### D. `reading_progress` 表增强
新增字段：
- `locator`

新增约束：
- `UNIQUE (user_id, book_id)`

### E. `book_notes` 表
新增基础笔记表

### F. PostgreSQL 扩展
启用：
- `pg_trgm`

---

## 1.3 Alembic upgrade 草案（伪代码）

```python
"""mvp scan/hash/reading/notes

Revision ID: 002
Revises: 001
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # 0) extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 1) enums
    hash_status_enum = sa.Enum(
        "pending", "done", "failed", "skipped",
        name="hashstatus"
    )
    scan_job_type_enum = sa.Enum(
        "scan_directory", "scan_file", "rehash", "resync_metadata",
        name="scanjobtype"
    )
    scan_job_status_enum = sa.Enum(
        "queued", "running", "completed", "failed", "partial_success", "cancelled",
        name="scanjobstatus"
    )
    scan_item_status_enum = sa.Enum(
        "queued", "processing", "created", "updated", "skipped", "failed",
        name="scanitemstatus"
    )

    bind = op.get_bind()
    hash_status_enum.create(bind, checkfirst=True)
    scan_job_type_enum.create(bind, checkfirst=True)
    scan_job_status_enum.create(bind, checkfirst=True)
    scan_item_status_enum.create(bind, checkfirst=True)

    # 2) books table columns
    op.add_column("books", sa.Column("content_hash", sa.String(length=128), nullable=True))
    op.add_column("books", sa.Column("hash_algorithm", sa.String(length=32), nullable=True))
    op.add_column("books", sa.Column("hash_status", hash_status_enum, nullable=False, server_default="pending"))
    op.add_column("books", sa.Column("hash_error", sa.Text(), nullable=True))
    op.add_column("books", sa.Column("file_mtime", sa.DateTime(), nullable=True))
    op.add_column("books", sa.Column("source_provider", sa.String(length=32), nullable=True))
    op.add_column("books", sa.Column("metadata_synced_at", sa.DateTime(), nullable=True))
    op.add_column("books", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))

    # remove default after backfill safety if needed
    op.alter_column("books", "hash_status", server_default=None)

    # 3) books indexes / constraints
    op.create_index("ix_books_content_hash", "books", ["content_hash"], unique=False)
    op.create_index("ix_books_file_path", "books", ["file_path"], unique=True)
    op.create_index(
        "ix_books_search_vector",
        "books",
        ["search_vector"],
        unique=False,
        postgresql_using="gin"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_title_trgm ON books USING gin (title gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_books_author_trgm ON books USING gin (author gin_trgm_ops)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_books_content_hash_not_null "
        "ON books (content_hash) WHERE content_hash IS NOT NULL"
    )

    # 4) scan_jobs table
    op.create_table(
        "scan_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", scan_job_type_enum, nullable=False),
        sa.Column("status", scan_job_status_enum, nullable=False),
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

    # 5) scan_job_items table
    op.create_table(
        "scan_job_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_format", sa.String(length=16), nullable=True),
        sa.Column("status", scan_item_status_enum, nullable=False),
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

    # 6) reading_progress enhancements
    op.add_column("reading_progress", sa.Column("locator", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_unique_constraint(
        "uq_reading_progress_user_book",
        "reading_progress",
        ["user_id", "book_id"]
    )

    # 7) book_notes table
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
```

---

## 1.4 Alembic downgrade 草案（伪代码）

```python
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
```

---

## 1.5 迁移实现注意点

### 注意点 A：`file_path` 唯一约束
当前初始迁移里 `books.file_path` 没有唯一索引：`backend/alembic/versions/001_initial.py:50-76`

如果你决定让 file_path 仍代表单文件位置，建议在 MVP 迁移中补：
- `UNIQUE(file_path)`

### 注意点 B：`reading_progress` 唯一约束可能因脏数据失败
在加 `UNIQUE(user_id, book_id)` 前，需要先清理重复数据。

建议迁移前先做检查 SQL：
```sql
SELECT user_id, book_id, COUNT(*)
FROM reading_progress
GROUP BY user_id, book_id
HAVING COUNT(*) > 1;
```

若有重复，迁移脚本前置清理策略：
- 保留 `updated_at` 最新的一条
- 删除其余记录

### 注意点 C：`search_vector` 初始回填
迁移完成后应回填：
```sql
UPDATE books
SET search_vector =
    setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(author, '')), 'B') ||
    setweight(to_tsvector('simple', coalesce(isbn, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(publisher, '')), 'C');
```

后续应用层在新增/更新图书时同步维护，或者 DB trigger 自动维护。

### 注意点 D：`JSONB` 兼容
当前旧表多用 `postgresql.JSON`，新字段建议直接用 `JSONB`：
- `reading_progress.locator`
- `book_notes.locator`

---

# 2. Pydantic Schema 设计稿

当前已有 schema：
- `BookBase`, `BookCreate`, `BookUpdate`, `Book`, `BookList`: `backend/app/schemas/book.py:6-46`
- `User*`: `backend/app/schemas/user.py:7-32`
- `Category*`: `backend/app/schemas/category.py:6-19`

MVP 需要新增：
1. 阅读进度 schema
2. 扫描任务 schema
3. 笔记 schema
4. 扩展图书 schema（暴露 hash / 状态字段时谨慎）

---

## 2.1 新文件建议

建议新增：
- `backend/app/schemas/reading.py`
- `backend/app/schemas/scanner.py`
- `backend/app/schemas/note.py`

并更新：
- `backend/app/schemas/__init__.py`

---

## 2.2 `reading.py` 草案

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from uuid import UUID
from app.models.reading import ReadingStatus


class PdfLocator(BaseModel):
    type: Literal["pdf_page"] = "pdf_page"
    page: int = Field(..., ge=1)
    offset: Optional[float] = Field(default=None, ge=0, le=1)


class EpubLocator(BaseModel):
    type: Literal["epub_cfi"] = "epub_cfi"
    cfi: str


class TxtLocator(BaseModel):
    type: Literal["text_offset"] = "text_offset"
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


ReadingLocator = Union[PdfLocator, EpubLocator, TxtLocator]


class ReadingProgressBase(BaseModel):
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[ReadingStatus] = None
    locator: Optional[ReadingLocator] = None


class ReadingProgressUpdate(ReadingProgressBase):
    pass


class ReadingProgressResponse(ReadingProgressBase):
    id: UUID
    user_id: UUID
    book_id: UUID
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecentReadingItem(BaseModel):
    book_id: UUID
    title: str
    cover_url: Optional[str] = None
    progress_percent: Optional[float] = None
    last_read_at: Optional[datetime] = None
    locator: Optional[ReadingLocator] = None


class RecentReadingList(BaseModel):
    items: list[RecentReadingItem]
```

### 设计说明
- `locator` 用 Union 做强类型校验
- `notes` / `bookmarks` 不再作为主接口字段输出
- `RecentReadingList` 直接服务前端“继续阅读”模块

---

## 2.3 `scanner.py` 草案

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


ScanJobType = Literal["scan_directory", "scan_file", "rehash", "resync_metadata"]
ScanJobStatus = Literal["queued", "running", "completed", "failed", "partial_success", "cancelled"]
ScanItemStatus = Literal["queued", "processing", "created", "updated", "skipped", "failed"]


class ScanDirectoryRequest(BaseModel):
    directory: str


class ScanFileRequest(BaseModel):
    file_path: str


class ScanJobResponse(BaseModel):
    id: UUID
    job_type: ScanJobType
    status: ScanJobStatus
    requested_path: str
    normalized_path: str
    total_items: int
    processed_items: int
    success_items: int
    failed_items: int
    skipped_items: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanJobListResponse(BaseModel):
    items: list[ScanJobResponse]
    total: int


class ScanJobItemResponse(BaseModel):
    id: UUID
    job_id: UUID
    file_path: str
    file_format: Optional[str] = None
    status: ScanItemStatus
    book_id: Optional[UUID] = None
    detected_hash: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanJobItemListResponse(BaseModel):
    items: list[ScanJobItemResponse]
    total: int


class ScanJobCreatedResponse(BaseModel):
    job_id: UUID
    status: ScanJobStatus
    message: str
```

---

## 2.4 `note.py` 草案

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from uuid import UUID


class PdfLocator(BaseModel):
    type: Literal["pdf_page"] = "pdf_page"
    page: int = Field(..., ge=1)
    offset: Optional[float] = Field(default=None, ge=0, le=1)


class EpubLocator(BaseModel):
    type: Literal["epub_cfi"] = "epub_cfi"
    cfi: str


class TxtLocator(BaseModel):
    type: Literal["text_offset"] = "text_offset"
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


NoteLocator = Union[PdfLocator, EpubLocator, TxtLocator]


class BookNoteCreate(BaseModel):
    locator: Optional[NoteLocator] = None
    note_text: str = Field(..., min_length=1, max_length=10000)


class BookNoteUpdate(BaseModel):
    locator: Optional[NoteLocator] = None
    note_text: Optional[str] = Field(default=None, min_length=1, max_length=10000)


class BookNoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    locator: Optional[NoteLocator] = None
    note_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookNoteListResponse(BaseModel):
    items: list[BookNoteResponse]
    total: int
```

---

## 2.5 `book.py` 的建议增强

当前 `Book` 返回太精简：`backend/app/schemas/book.py:27-46`

MVP 可以考虑增加一个**面向后台**的 schema，而不是直接污染普通 `Book` 返回：

```python
class AdminBook(Book):
    file_path: str
    isbn: Optional[str] = None
    hash_status: Optional[str] = None
    content_hash: Optional[str] = None
    indexed_at: Optional[datetime] = None
    metadata_synced_at: Optional[datetime] = None
```

### 原则
- 面向普通用户的 `Book` 响应：尽量不暴露 `file_path`
- 面向后台的 `AdminBook`：允许暴露本地路径与 hash 状态

---

## 2.6 `__init__.py` 导出草案

建议更新 `backend/app/schemas/__init__.py`

```python
from app.schemas.user import User, UserCreate, UserLogin, Token
from app.schemas.book import Book, BookCreate, BookUpdate, BookList
from app.schemas.category import Category, CategoryCreate
from app.schemas.reading import ReadingProgressUpdate, ReadingProgressResponse, RecentReadingList
from app.schemas.note import BookNoteCreate, BookNoteUpdate, BookNoteResponse, BookNoteListResponse
from app.schemas.scanner import (
    ScanDirectoryRequest,
    ScanFileRequest,
    ScanJobCreatedResponse,
    ScanJobResponse,
    ScanJobListResponse,
    ScanJobItemResponse,
    ScanJobItemListResponse,
)

__all__ = [
    "User", "UserCreate", "UserLogin", "Token",
    "Book", "BookCreate", "BookUpdate", "BookList",
    "Category", "CategoryCreate",
    "ReadingProgressUpdate", "ReadingProgressResponse", "RecentReadingList",
    "BookNoteCreate", "BookNoteUpdate", "BookNoteResponse", "BookNoteListResponse",
    "ScanDirectoryRequest", "ScanFileRequest", "ScanJobCreatedResponse",
    "ScanJobResponse", "ScanJobListResponse", "ScanJobItemResponse", "ScanJobItemListResponse",
]
```

---

# 3. 与路由的对应关系

## 3.1 Scanner
建议新路由使用：
- `ScanDirectoryRequest`
- `ScanFileRequest`
- `ScanJobCreatedResponse`
- `ScanJobResponse`
- `ScanJobItemListResponse`

## 3.2 Reading Progress
建议新路由使用：
- `ReadingProgressUpdate`
- `ReadingProgressResponse`
- `RecentReadingList`

## 3.3 Notes
建议新路由使用：
- `BookNoteCreate`
- `BookNoteUpdate`
- `BookNoteResponse`
- `BookNoteListResponse`

---

# 4. 推荐实施顺序

## 第一步：迁移
先做 Alembic 迁移，确保 DB 能支撑后续功能

顺序：
1. `books` 扩字段
2. `scan_jobs`
3. `scan_job_items`
4. `reading_progress.locator`
5. `reading_progress` 唯一约束
6. `book_notes`
7. FTS / trigram 索引

## 第二步：模型
更新 ORM：
- `Book`
- `ReadingProgress`
- 新增 `ScanJob`
- 新增 `ScanJobItem`
- 新增 `BookNote`

## 第三步：Schema
新增：
- `reading.py`
- `scanner.py`
- `note.py`

## 第四步：API
按优先级接：
1. scanner jobs
2. reading progress
3. notes
4. books 搜索增强

---

# 5. 结论

这套迁移 + schema 草案，已经足够支持 MVP：
- hash 入库
- 任务化扫描
- 搜索增强
- Web 阅读进度同步
- 基础笔记
- 后台管理 API

并且保持了对现有代码的**最小侵入**。
