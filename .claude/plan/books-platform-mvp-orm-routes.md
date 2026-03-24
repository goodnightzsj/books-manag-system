# Books Platform MVP - ORM Model Draft + FastAPI Route Draft

## 0. 目标

基于当前项目结构，为 MVP 产出：
1. ORM 模型草案
2. FastAPI 路由草案

要求：
- 贴合现有代码风格
- 尽量复用现有文件布局
- 对现有模块侵入最小

参考：
- Router 聚合：`backend/app/api/router.py:1-11`
- Models 导出：`backend/app/models/__init__.py:1-5`
- Auth 依赖：`backend/app/api/deps.py:1-40`
- Files 路由：`backend/app/api/files.py:1-125`

---

# 1. ORM 模型草案

## 1.1 现有模型保留策略

### 保留
- `User`：`backend/app/models/user.py`
- `Book` / `Category`：`backend/app/models/book.py`
- `ReadingProgress`：`backend/app/models/reading.py`

### 新增
- `ScanJob`
- `ScanJobItem`
- `BookNote`

### 修改
- `Book`
- `ReadingProgress`
- `models/__init__.py`

---

## 1.2 `Book` 模型草案

> 文件建议：继续放在 `backend/app/models/book.py`

### 新增枚举
```python
class HashStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### `Book` 新增字段草案
```python
content_hash = Column(String, nullable=True, index=True)
hash_algorithm = Column(String, nullable=True)
hash_status = Column(Enum(HashStatus), default=HashStatus.PENDING, nullable=False)
hash_error = Column(Text)
file_mtime = Column(DateTime)
source_provider = Column(String)
metadata_synced_at = Column(DateTime)
search_vector = Column(TSVECTOR)
```

### 模型示意
```python
class Book(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    subtitle = Column(String)
    author = Column(String, index=True)
    publisher = Column(String)
    publish_date = Column(DateTime)
    isbn = Column(String, unique=True, index=True)
    description = Column(Text)
    cover_url = Column(String)
    file_path = Column(String, nullable=False, unique=True)
    file_format = Column(Enum(FileFormat), nullable=False)
    file_size = Column(BigInteger)
    file_mtime = Column(DateTime)

    content_hash = Column(String, index=True)
    hash_algorithm = Column(String)
    hash_status = Column(Enum(HashStatus), default=HashStatus.PENDING, nullable=False)
    hash_error = Column(Text)

    language = Column(String, default="zh")
    page_count = Column(Integer)
    rating = Column(Float)
    rating_count = Column(Integer)
    tags = Column(JSON, default=list)
    book_metadata = Column(JSON, default=dict)
    source_provider = Column(String)
    metadata_synced_at = Column(DateTime)
    search_vector = Column(TSVECTOR)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    indexed_at = Column(DateTime)

    categories = relationship("Category", secondary=book_category, back_populates="books")
    reading_progress = relationship("ReadingProgress", back_populates="book", cascade="all, delete-orphan")
    notes = relationship("BookNote", back_populates="book", cascade="all, delete-orphan")
```

### 设计说明
- `search_vector` 属于 PostgreSQL 专用字段，ORM 中可按项目现状决定是否显式声明；如果不声明，也可只在迁移与查询层使用。
- `file_path` 建议加唯一约束。
- `content_hash` 建议加部分唯一索引，而不是 ORM 里直接 `unique=True`。

---

## 1.3 `ReadingProgress` 模型草案

> 文件建议：继续放在 `backend/app/models/reading.py`

### 建议增强
```python
from sqlalchemy.dialects.postgresql import JSONB
```

```python
locator = Column(JSONB)
```

### 模型示意
```python
class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_reading_progress_user_book"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)
    current_page = Column(Integer)
    total_pages = Column(Integer)
    progress_percent = Column(Float, default=0.0)
    status = Column(Enum(ReadingStatus), default=ReadingStatus.NOT_STARTED, nullable=False)
    locator = Column(JSONB)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    last_read_at = Column(DateTime)
    notes = Column(Text)  # legacy
    bookmarks = Column(JSON)  # legacy
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book", back_populates="reading_progress")
```

### 设计说明
- `notes` / `bookmarks` 先保留，避免立即破坏旧逻辑
- 新接口优先使用 `locator` 和独立 `BookNote`

---

## 1.4 `ScanJob` 模型草案

> 新文件建议：`backend/app/models/scan_job.py`

```python
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base


class ScanJobType(str, enum.Enum):
    SCAN_DIRECTORY = "scan_directory"
    SCAN_FILE = "scan_file"
    REHASH = "rehash"
    RESYNC_METADATA = "resync_metadata"


class ScanJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(Enum(ScanJobType), nullable=False)
    status = Column(Enum(ScanJobStatus), nullable=False, default=ScanJobStatus.QUEUED)
    requested_path = Column(Text, nullable=False)
    normalized_path = Column(Text, nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    processed_items = Column(Integer, default=0, nullable=False)
    success_items = Column(Integer, default=0, nullable=False)
    failed_items = Column(Integer, default=0, nullable=False)
    skipped_items = Column(Integer, default=0, nullable=False)
    error_message = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    items = relationship("ScanJobItem", back_populates="job", cascade="all, delete-orphan")
```

---

## 1.5 `ScanJobItem` 模型草案

> 新文件建议：`backend/app/models/scan_job.py`

```python
class ScanItemStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


class ScanJobItem(Base):
    __tablename__ = "scan_job_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_format = Column(String, nullable=True)
    status = Column(Enum(ScanItemStatus), nullable=False, default=ScanItemStatus.QUEUED)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    detected_hash = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    job = relationship("ScanJob", back_populates="items")
```

---

## 1.6 `BookNote` 模型草案

> 新文件建议：`backend/app/models/note.py`

```python
from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class BookNote(Base):
    __tablename__ = "book_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)
    locator = Column(JSONB)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    book = relationship("Book", back_populates="notes")
    user = relationship("User")
```

---

## 1.7 `models/__init__.py` 草案

当前：`backend/app/models/__init__.py:1-5`

建议改为：

```python
from app.models.user import User
from app.models.book import Book, Category
from app.models.reading import ReadingProgress
from app.models.scan_job import ScanJob, ScanJobItem
from app.models.note import BookNote

__all__ = [
    "User",
    "Book",
    "Category",
    "ReadingProgress",
    "ScanJob",
    "ScanJobItem",
    "BookNote",
]
```

---

# 2. FastAPI 路由草案

## 2.1 路由组织原则

当前聚合：`backend/app/api/router.py:1-11`

MVP 建议新增 3 个 router：
- `reading_progress.py`
- `notes.py`
- `scanner_jobs.py`（或继续复用 `scanner.py`）

### 推荐做法
为了减少破坏：
- **保留现有 `scanner.py` 文件**，但将其语义改成 job 化 API
- 新增：
  - `reading_progress.py`
  - `notes.py`

---

## 2.2 `scanner.py` 路由草案（MVP 改造版）

> 建议仍使用 `prefix="/scanner"`

### 路由列表
| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/scanner/jobs/directory` | 管理员 | 创建目录扫描任务 |
| POST | `/scanner/jobs/file` | 管理员 | 创建单文件扫描任务 |
| GET | `/scanner/jobs` | 管理员 | 查询任务列表 |
| GET | `/scanner/jobs/{job_id}` | 管理员 | 查询任务详情 |
| GET | `/scanner/jobs/{job_id}/items` | 管理员 | 查询任务明细 |
| POST | `/scanner/jobs/{job_id}/retry-failed` | 管理员 | 重试失败项 |
| POST | `/scanner/books/{book_id}/metadata-sync` | 管理员 | 同步图书元数据 |
| POST | `/scanner/books/{book_id}/extract-cover` | 管理员 | 提取图书封面 |

### 推荐函数签名
```python
@router.post("/jobs/directory", response_model=ScanJobCreatedResponse)
def create_directory_scan_job(...):
    ...

@router.get("/jobs/{job_id}", response_model=ScanJobResponse)
def get_scan_job(...):
    ...

@router.get("/jobs/{job_id}/items", response_model=ScanJobItemListResponse)
def get_scan_job_items(...):
    ...
```

### 设计说明
- 不建议保留原 `POST /scanner/scan-directory` 这种 fire-and-forget 语义
- 统一迁到 `/scanner/jobs/*`
- 旧接口如需兼容，可临时保留并内部转发到 job 创建逻辑

---

## 2.3 `reading_progress.py` 路由草案

> 新文件：`backend/app/api/reading_progress.py`

### 路由列表
| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/reading-progress/{book_id}` | 用户 | 获取当前用户该书进度 |
| PUT | `/reading-progress/{book_id}` | 用户 | 更新当前用户该书进度 |
| GET | `/reading-progress/recent` | 用户 | 最近阅读列表 |

### 推荐函数签名
```python
router = APIRouter(prefix="/reading-progress", tags=["ReadingProgress"])

@router.get("/{book_id}", response_model=ReadingProgressResponse)
def get_reading_progress(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...

@router.put("/{book_id}", response_model=ReadingProgressResponse)
def upsert_reading_progress(
    book_id: UUID,
    payload: ReadingProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...

@router.get("/recent", response_model=RecentReadingList)
def get_recent_readings(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

### 行为建议
- `PUT` 采用 upsert 语义
- 若记录不存在则创建，存在则更新
- 更新时自动刷新 `last_read_at`
- 若 `progress_percent >= 100`，可自动置 `status=completed`

---

## 2.4 `notes.py` 路由草案

> 新文件：`backend/app/api/notes.py`

### 路由列表
| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/books/{book_id}/notes` | 用户 | 当前用户该书笔记列表 |
| POST | `/books/{book_id}/notes` | 用户 | 创建笔记 |
| PUT | `/books/{book_id}/notes/{note_id}` | 用户 | 编辑笔记 |
| DELETE | `/books/{book_id}/notes/{note_id}` | 用户 | 删除笔记 |

### 推荐函数签名
```python
router = APIRouter(prefix="/books", tags=["Notes"])

@router.get("/{book_id}/notes", response_model=BookNoteListResponse)
def get_book_notes(...):
    ...

@router.post("/{book_id}/notes", response_model=BookNoteResponse, status_code=201)
def create_book_note(...):
    ...

@router.put("/{book_id}/notes/{note_id}", response_model=BookNoteResponse)
def update_book_note(...):
    ...

@router.delete("/{book_id}/notes/{note_id}", status_code=204)
def delete_book_note(...):
    ...
```

### 权限建议
- 用户只能访问自己的笔记
- 管理员不需要默认越权读所有人笔记，避免未来隐私问题

---

## 2.5 `books.py` 路由草案（MVP 改造点）

> 现有文件：`backend/app/api/books.py:1-113`

### 保留的路由
- `GET /books`
- `GET /books/{book_id}`
- `POST /books`
- `PUT /books/{book_id}`
- `DELETE /books/{book_id}`

### 需要改造的点
#### `GET /books`
当前：
- 只支持 `search` 和 `author`
- 只用 `ILIKE`

MVP 建议支持：
- `q`
- `author`
- `category_id`
- `format`
- `sort`
- `order`

#### 推荐函数签名
```python
@router.get("", response_model=BookList)
def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    author: Optional[str] = None,
    category_id: Optional[UUID] = None,
    format: Optional[str] = None,
    sort: str = Query("updated_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

### 后台专用补充接口（可选）
如果不想把 metadata/cover 操作放在 scanner 下，也可以放 books 下：
- `POST /books/{book_id}/metadata-sync`
- `POST /books/{book_id}/extract-cover`

但从当前代码职责看，继续放在 `scanner.py` 更自然。

---

## 2.6 `files.py` 路由草案（MVP 改造点）

> 现有文件：`backend/app/api/files.py:1-125`

### 保留
- `GET /files/download/{book_id}`
- `GET /files/stream/{book_id}`
- `GET /files/cover/{book_id}`

### 修改建议
#### `stream_book`
当前：
- 手动 chunk 返回 `StreamingResponse`
- 没有标准 Range 支持

MVP 建议：
- 优先支持 `Range` 请求
- 若实现成本太高，至少确保 PDF.js 能稳定读取

### 新增可选接口
- `HEAD /files/stream/{book_id}`
  - 用于前端预读取文件元信息

---

## 2.7 `api/router.py` 聚合草案

当前：`backend/app/api/router.py:1-11`

建议改为：

```python
from fastapi import APIRouter
from app.api import auth, books, scanner, categories, recommendations, files, reading_progress, notes

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(scanner.router)
api_router.include_router(categories.router)
api_router.include_router(recommendations.router)
api_router.include_router(files.router)
api_router.include_router(reading_progress.router)
api_router.include_router(notes.router)
```

---

# 3. 推荐文件落位

## Models
- `backend/app/models/book.py` → 修改 `Book`，新增 `HashStatus`
- `backend/app/models/reading.py` → 修改 `ReadingProgress`
- `backend/app/models/scan_job.py` → 新增 `ScanJob` / `ScanJobItem`
- `backend/app/models/note.py` → 新增 `BookNote`
- `backend/app/models/__init__.py` → 更新导出

## API
- `backend/app/api/books.py` → 搜索增强
- `backend/app/api/scanner.py` → 改 job 化
- `backend/app/api/reading_progress.py` → 新增
- `backend/app/api/notes.py` → 新增
- `backend/app/api/router.py` → 聚合新增路由

---

# 4. 推荐实现顺序

1. 先完成 Alembic 迁移
2. 再更新 ORM 模型
3. 再写 Pydantic schema
4. 再写 `reading_progress.py`
5. 再改 `scanner.py`
6. 再写 `notes.py`
7. 最后改 `books.py` 和 `files.py`

---

# 5. 结论

这套 ORM + FastAPI 草案有几个优点：
- 保持现有目录结构与编码风格
- 不要求立即拆大模型
- 能直接支撑 MVP：hash、job、进度、笔记、搜索、下载
- 后续升级到 `book_files` / `annotations` / `bookmarks` 时也不会推翻当前设计
