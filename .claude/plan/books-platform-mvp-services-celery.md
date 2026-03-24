# 📋 实施计划：Books Platform MVP 服务层与 Celery 任务规划

### 任务类型
- [ ] 前端 (→ Gemini)
- [x] 后端 (→ Codex)
- [ ] 全栈 (→ 并行)

## 技术方案

延续当前 `backend/` 同步栈，不做整栈重写；采用 **thin tasks, thick services**：
- **Celery task** 只负责认领任务、创建 DB session、调用 service、更新状态
- **Service layer** 负责领域规则、幂等、去重、状态流转、错误归类
- **PostgreSQL** 作为 `scan_jobs` / `scan_job_items` / `books.hash_status` 的唯一真相源
- **Redis** 只承担 broker，不把 Celery result backend 当对外进度 API

与当前基线的衔接点：
- 当前扫描入口仍是 `BackgroundTasks`：`backend/app/api/scanner.py:42-56`
- 当前扫描逻辑把目录遍历、判重、入库揉在一起：`backend/app/services/scanner_service.py:30-128`
- 当前路径判重仍是 `file_path + file_size`：`backend/app/services/scanner_service.py:72-77`
- 当前 metadata / cover 还是薄工具类：`backend/app/services/metadata_service.py:10-193`、`backend/app/services/cover_service.py:12-98`

---

## 服务层草案

### 1. 分层原则

1. Router 只做鉴权、参数校验、调用 service、返回 schema
2. Celery task 不写业务规则，只做编排与状态落库
3. `scan_jobs` / `scan_job_items` 只能通过 `ScanJobService` 修改
4. 图书去重、hash 写回、重复书合并只能通过 `BookIngestService`
5. 搜索向量更新统一通过 `BookSearchService`
6. 阅读进度与笔记保持同步 API，不强行异步化

### 2. 服务职责划分

| 服务 | 文件建议 | 主要职责 | 直接依赖 |
|---|---|---|---|
| `FileAccessService` | `backend/app/services/file_access_service.py` | 路径规范化、安全校验、目录遍历、文件 stat、媒体类型判断、后续 Range 支持 | `settings`, `pathlib`, `os` |
| `ScanJobService` | `backend/app/services/scan_job_service.py` | 创建/认领/收尾 `scan_jobs`、维护 `scan_job_items`、计数器与状态流转 | `Session`, `ScanJob`, `ScanJobItem` |
| `ScanService` | `backend/app/services/scanner_service.py` | 单个扫描项业务编排：本地 metadata、book upsert、搜索刷新、后续 hash 分发 | `FileAccessService`, `LocalMetadataService`, `BookIngestService`, `BookSearchService` |
| `BookIngestService` | `backend/app/services/book_ingest_service.py` | `Book` create/update、hash 写回、内容去重、重复书合并 | `Session`, `Book`, `Category`, `ReadingProgress`, `BookNote` |
| `HashService` | `backend/app/services/hash_service.py` | quick fingerprint、sha256 计算、是否需要重算 hash、错误归类 | `hashlib`, `os` |
| `LocalMetadataService` | `backend/app/services/metadata_service.py` | 本地文件 metadata 提取（PDF/EPUB/TXT 等） | `PyPDF2`, `ebookmeta` |
| `MetadataSyncService` | `backend/app/services/metadata_service.py` | 外部 provider 调用顺序、字段归并、`source_provider` / `metadata_synced_at` 写回 | `OnlineMetadataService`, `BookSearchService`, `CoverSyncService` |
| `CoverSyncService` | `backend/app/services/cover_service.py` | 本地提取封面、远程下载封面、缩略图生成、封面存在性判断 | `PIL`, `fitz`, `httpx` |
| `BookSearchService` | `backend/app/services/search_service.py` | FTS + trigram 查询、分页排序、`search_vector` 刷新 | `Session`, SQLAlchemy, PostgreSQL FTS |
| `ReadingProgressService` | `backend/app/services/reading_service.py` | 获取/更新当前用户阅读进度、recent 列表、状态衍生规则 | `ReadingProgress`, `Book` |
| `BookNoteService` | `backend/app/services/note_service.py` | 当前用户笔记 CRUD、按书过滤、权限隔离 | `BookNote`, `Book` |
| `TaskDispatchService` | `backend/app/services/task_dispatch_service.py` | 唯一负责 Celery `.delay()` / `apply_async()` | `backend/app/tasks/*` |

### 3. 关键方法签名建议

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Literal
from uuid import UUID

@dataclass(slots=True)
class DiscoveredFile:
    path: str
    extension: str
    file_format: str

@dataclass(slots=True)
class FileSnapshot:
    path: str
    extension: str
    file_format: str
    size: int
    mtime: datetime

@dataclass(slots=True)
class BookUpsertResult:
    book_id: UUID
    action: Literal["created", "updated", "skipped"]
    should_hash: bool
    should_extract_cover: bool
```

```python
class ScanJobService:
    def create_job(self, *, job_type: str, requested_path: str, normalized_path: str, created_by: UUID | None) -> ScanJob: ...
    def claim_job(self, job_id: UUID) -> ScanJob | None: ...
    def add_items(self, job_id: UUID, files: list[DiscoveredFile]) -> list[ScanJobItem]: ...
    def claim_item(self, item_id: UUID) -> ScanJobItem | None: ...
    def mark_item_processing(self, item_id: UUID) -> None: ...
    def mark_item_finished(self, item_id: UUID, *, status: str, book_id: UUID | None = None, detected_hash: str | None = None, error_message: str | None = None) -> None: ...
    def maybe_finalize_job(self, job_id: UUID) -> str: ...
    def retry_failed_items(self, job_id: UUID) -> int: ...
```

```python
class FileAccessService:
    def resolve_scan_root(self, requested_path: str) -> str: ...
    def resolve_book_file(self, file_path: str) -> str: ...
    def iter_supported_files(self, root_path: str) -> Iterable[DiscoveredFile]: ...
    def snapshot(self, file_path: str) -> FileSnapshot: ...
    def guess_media_type(self, file_format: str) -> str: ...
```

```python
class ScanService:
    def process_file(self, file_path: str) -> BookUpsertResult: ...

class BookIngestService:
    def upsert_scanned_book(self, snapshot: FileSnapshot, metadata: dict[str, Any]) -> BookUpsertResult: ...
    def apply_hash_result(self, *, book_id: UUID, content_hash: str, algorithm: str, file_mtime: datetime, file_size: int) -> UUID: ...
    def merge_duplicate_books(self, *, source_book_id: UUID, target_book_id: UUID) -> UUID: ...

class HashService:
    def should_hash(self, snapshot: FileSnapshot, book: Book) -> bool: ...
    def compute_sha256(self, file_path: str, chunk_size: int = 1024 * 1024) -> str: ...
```

```python
class MetadataSyncService:
    def sync_book(self, book_id: UUID, *, force: bool = False) -> Book: ...

class CoverSyncService:
    def ensure_cover(self, book_id: UUID, *, prefer_remote: bool = False, source_url: str | None = None, force: bool = False) -> str | None: ...

class BookSearchService:
    def search_books(self, *, q: str | None, author: str | None, category_id: UUID | None, file_format: str | None, sort: str, order: str, page: int, page_size: int) -> tuple[list[Book], int]: ...
    def refresh_document(self, book_id: UUID) -> None: ...
```

```python
class ReadingProgressService:
    def get_for_user(self, user_id: UUID, book_id: UUID) -> ReadingProgress | None: ...
    def upsert_for_user(self, user_id: UUID, book_id: UUID, payload: ReadingProgressUpdate) -> ReadingProgress: ...
    def list_recent_for_user(self, user_id: UUID, limit: int = 10) -> list[ReadingProgress]: ...

class BookNoteService:
    def list_for_book(self, user_id: UUID, book_id: UUID) -> list[BookNote]: ...
    def create_for_book(self, user_id: UUID, book_id: UUID, payload: BookNoteCreate) -> BookNote: ...
    def update_note(self, user_id: UUID, book_id: UUID, note_id: UUID, payload: BookNoteUpdate) -> BookNote: ...
    def delete_note(self, user_id: UUID, book_id: UUID, note_id: UUID) -> None: ...
```

```python
class TaskDispatchService:
    def enqueue_scan_directory(self, job_id: UUID) -> str: ...
    def enqueue_scan_file(self, job_id: UUID) -> str: ...
    def enqueue_process_scan_item(self, item_id: UUID) -> str: ...
    def enqueue_retry_failed_items(self, job_id: UUID) -> str: ...
    def enqueue_rehash_job(self, job_id: UUID) -> str: ...
    def enqueue_compute_hash(self, book_id: UUID, *, item_id: UUID | None = None) -> str: ...
    def enqueue_metadata_sync(self, book_id: UUID, *, job_id: UUID | None = None) -> str: ...
    def enqueue_cover_sync(self, book_id: UUID, *, prefer_remote: bool = False) -> str: ...
```

### 4. 调用关系

#### 4.1 目录扫描主链路
1. `POST /api/v1/scanner/jobs/directory`
2. `FileAccessService.resolve_scan_root()` 做路径校验与规范化
3. `ScanJobService.create_job()` 写入 `scan_jobs`
4. `TaskDispatchService.enqueue_scan_directory(job_id)` 分发 root task
5. `scan.run_directory_job(job_id)` 负责发现文件并创建 `scan_job_items`
6. `scan.process_scan_item(item_id)` 逐个处理文件
7. `ScanService.process_file()` 编排本地 metadata、book upsert、搜索刷新
8. 如需补 hash，分发 `hash.compute_book_hash(book_id)`
9. `ScanJobService.mark_item_finished()` 和 `maybe_finalize_job()` 负责 item/job 收尾

#### 4.2 单个扫描项内部链路
```text
FileAccessService.snapshot
  -> LocalMetadataService.extract
  -> BookIngestService.upsert_scanned_book
  -> BookSearchService.refresh_document
  -> ScanJobService.mark_item_finished
  -> TaskDispatchService.enqueue_compute_hash (optional)
```

#### 4.3 hash 去重链路
```text
HashService.compute_sha256
  -> BookIngestService.apply_hash_result
     -> find duplicate by content_hash
     -> choose canonical book
     -> merge_duplicate_books
     -> update hash_status/content_hash/file_path/file_mtime
```

#### 4.4 单书 metadata / cover 链路
```text
MetadataSyncService.sync_book
  -> OnlineMetadataService.fetch_best_match
  -> merge provider fields into books
  -> BookSearchService.refresh_document
  -> CoverSyncService.ensure_cover (optional)
```

### 5. 错误处理原则

- **路径错误 / 越界访问**：由 `FileAccessService` 抛业务错误，API 返回 400/403
- **文件损坏 / 不支持格式**：只标记 `scan_job_items.failed`，不让整个 job 崩掉
- **hash 失败**：写回 `books.hash_status=failed` 与 `hash_error`，不回滚已创建的 `Book`
- **metadata 外部接口失败**：保留当前图书字段，不清空旧数据
- **重复书合并**：只允许在 `BookIngestService.merge_duplicate_books()` 内执行；必须在一个事务中重绑 `reading_progress`、`book_notes`、`book_categories`、相关 `scan_job_items.book_id`

---

## Celery 任务设计草案

### 1. 设计原则

1. **PostgreSQL 是任务状态真相源**；Celery 状态只用于 worker 内部执行
2. **一任务一 Session**；禁止把 API session 传入 Celery
3. **先认领、后执行**；没有认领到 job/item 的任务直接 no-op
4. **任务薄、服务厚**；所有业务规则收口到 service
5. **失败不吞**；错误信息必须落 `scan_jobs.error_message` 或 `scan_job_items.error_message`

### 2. 推荐队列划分

| 队列 | 任务类型 | 说明 |
|---|---|---|
| `scan` | 目录扫描、单文件扫描、扫描项处理、失败项重试 | I/O 较多，吞吐优先 |
| `enrich` | hash、metadata、cover | 外部 API / CPU / 文件处理 |
| `maintenance` | stalled job reconcile、定时修复 | beat 定时任务 |

### 3. 任务清单

| 任务名 | 队列 | 输入 | 输出 | 幂等性 | 重试/超时 | 失败补偿 |
|---|---|---|---|---|---|---|
| `scan.run_directory_job` | `scan` | `job_id` | 只更新 DB | `claim_job()` 仅允许 `queued` 认领 | `max_retries=1`，`retry_backoff=60s`，`soft=1800s`，`hard=2100s` | 标记 job `failed`，写 `error_message` |
| `scan.run_file_job` | `scan` | `job_id` | 同上 | 同上 | `max_retries=1`，`retry_backoff=30s`，`soft=300s`，`hard=420s` | 标记 job `failed` |
| `scan.process_scan_item` | `scan` | `item_id` | 更新 item/book/search | `claim_item()` 仅允许 `queued/failed` 认领 | `max_retries=2`，`retry_backoff=15s`，`soft=120s`，`hard=180s` | 标记 item `failed`，job 进入 `partial_success` 候选 |
| `scan.retry_failed_items` | `scan` | `job_id` | 重新排队失败项 | 只重置当前 `failed` 项 | `max_retries=1`，`retry_backoff=30s`，`soft=300s`，`hard=420s` | 无需回滚，保留原失败记录 |
| `hash.compute_book_hash` | `enrich` | `book_id`, `item_id?` | 写回 `content_hash/hash_status` | 已完成且 `size/mtime` 未变化则跳过 | `max_retries=2`，`retry_backoff=30s`，`soft=600s`，`hard=900s` | `hash_status=failed` + `hash_error` |
| `metadata.sync_book_metadata` | `enrich` | `book_id`, `force=False`, `job_id?` | 写回 metadata/provider | `force=False` 且近期已同步可跳过 | `max_retries=3`，指数退避 + jitter，`soft=90s`，`hard=120s` | 保留旧 metadata，不清空字段 |
| `cover.extract_or_download_cover` | `enrich` | `book_id`, `prefer_remote=False`, `source_url?`, `force=False` | 写回 `cover_url` | 已有封面且非 `force` 则跳过 | `max_retries=2`，`retry_backoff=30s`，`soft=120s`，`hard=180s` | 仅记录错误，不影响图书主记录 |
| `maintenance.reconcile_stalled_jobs` | `maintenance` | `max_item_age_minutes=15` | 修复卡住状态 | 天然幂等 | `max_retries=1`，`soft=60s`，`hard=120s` | 将异常项标 `failed` 或重排队 |

### 4. 任务与 `scan_jobs` / `scan_job_items` 的关系

#### 4.1 `scan_jobs`
- 表示用户可见的“一个后台请求”
- 类型包含：`scan_directory`、`scan_file`、`rehash`、`resync_metadata`
- 只记录任务级状态与聚合计数

#### 4.2 `scan_job_items`
- 表示可独立重试的最小处理单元
- 目录扫描：一文件一 item
- 单文件扫描：一个 job 对应一个 item
- `rehash`：一个 job 可对应一批图书/文件 item
- `resync_metadata`：单书同步时也建议创建单 item，复用统一观测能力

#### 4.3 计数器更新规则
- `total_items`：发现文件或批量创建 item 时增加
- `processed_items`：item 进入终态时增加
- `success_items`：`created` / `updated`
- `skipped_items`：`skipped`
- `failed_items`：`failed`
- `status`：
  - 全成功 -> `completed`
  - 部分失败 -> `partial_success`
  - 全失败或 root task 崩溃 -> `failed`

### 5. 链路编排建议

#### 5.1 推荐主链路
```text
POST /scanner/jobs/directory
  -> create scan_jobs row
  -> enqueue scan.run_directory_job(job_id)

scan.run_directory_job(job_id)
  -> claim job
  -> discover supported files
  -> create scan_job_items rows
  -> enqueue scan.process_scan_item(item_id) for each item

scan.process_scan_item(item_id)
  -> claim item
  -> process file through services
  -> refresh search document
  -> mark item finished
  -> optionally enqueue hash.compute_book_hash(book_id)
  -> maybe_finalize_job(job_id)
```

#### 5.2 hash 链路
```text
hash.compute_book_hash(book_id)
  -> compute sha256
  -> apply hash result
  -> merge duplicate books if needed
  -> update item.detected_hash (if item_id exists)
```

#### 5.3 metadata / cover 链路
```text
POST /scanner/books/{book_id}/metadata-sync
  -> create resync_metadata job (recommended)
  -> enqueue metadata.sync_book_metadata(book_id)
  -> metadata service may enqueue cover.extract_or_download_cover(book_id)
```

### 6. 哪些操作同步，哪些异步

#### 同步保留
- `POST /scanner/jobs/*`：只创建 job，不做真实扫描
- `GET /scanner/jobs` / `GET /scanner/jobs/{job_id}` / `GET /scanner/jobs/{job_id}/items`
- `GET /books` / `GET /books/{book_id}` / 图书基础 CRUD
- `GET/PUT /reading-progress/{book_id}`
- `GET/POST/PUT/DELETE /books/{book_id}/notes`
- `GET /files/download/{book_id}` / `GET /files/stream/{book_id}` / `GET /files/cover/{book_id}`
- `BookSearchService.refresh_document()`：建议在事务内同步执行，保证搜索可见性稳定

#### 异步执行
- 目录扫描 / 单文件扫描
- 失败项重试
- 批量 rehash
- 外部 metadata 同步
- 封面提取 / 下载
- stalled job 定时修复

#### 可选混合
- 单书封面提取在 MVP v1 可保留同步，但 service 设计必须兼容后续异步化

---

## 推荐模块 / 文件落位

```text
backend/app/
  celery_app.py
  api/
    books.py
    scanner.py
    reading_progress.py
    notes.py
  models/
    book.py
    reading.py
    scan_job.py
    note.py
  schemas/
    book.py
    reading.py
    scanner.py
    note.py
  services/
    __init__.py
    file_access_service.py
    scan_job_service.py
    scanner_service.py
    book_ingest_service.py
    hash_service.py
    metadata_service.py
    cover_service.py
    search_service.py
    reading_service.py
    note_service.py
    task_dispatch_service.py
  tasks/
    __init__.py
    scan_tasks.py
    hash_tasks.py
    metadata_tasks.py
    cover_tasks.py
    maintenance_tasks.py
```

### 文件说明

| 文件 | 操作 | 说明 |
|---|---|---|
| `backend/app/celery_app.py` | 新增 | Celery app 初始化、队列与 beat 配置 |
| `backend/app/services/file_access_service.py` | 新增 | 安全路径解析、目录遍历、文件 stat、MIME / Range 辅助 |
| `backend/app/services/scan_job_service.py` | 新增 | 统一管理 `scan_jobs` / `scan_job_items` |
| `backend/app/services/scanner_service.py` | 修改 | 从“目录扫描大类”收敛为 `ScanService`，只保留单 item 编排 |
| `backend/app/services/book_ingest_service.py` | 新增 | `Book` upsert、hash 写回、重复书合并 |
| `backend/app/services/hash_service.py` | 新增 | quick fingerprint、sha256、hash 决策 |
| `backend/app/services/metadata_service.py` | 修改 | 保留本地提取，同时新增在线同步逻辑 |
| `backend/app/services/cover_service.py` | 修改 | 从工具类提升为 `CoverSyncService` |
| `backend/app/services/search_service.py` | 新增 | PostgreSQL FTS / trigram 搜索与向量刷新 |
| `backend/app/services/reading_service.py` | 新增 | 阅读进度查询、upsert、recent |
| `backend/app/services/note_service.py` | 新增 | 用户笔记 CRUD |
| `backend/app/services/task_dispatch_service.py` | 新增 | Celery 分发统一出口 |
| `backend/app/tasks/scan_tasks.py` | 新增 | root scan tasks + item tasks + retry tasks |
| `backend/app/tasks/hash_tasks.py` | 新增 | hash 计算与 dedup task |
| `backend/app/tasks/metadata_tasks.py` | 新增 | metadata 同步 task |
| `backend/app/tasks/cover_tasks.py` | 新增 | 封面提取 / 下载 task |
| `backend/app/tasks/maintenance_tasks.py` | 新增 | stalled job reconcile 等定时任务 |
| `backend/app/api/scanner.py` | 修改 | 从 `BackgroundTasks` 改为 job 创建 / 查询 / 重试接口 |
| `backend/app/api/books.py` | 修改 | 接 `BookSearchService`，后续接 metadata/cover 管理入口 |
| `backend/app/api/reading_progress.py` | 新增 | 阅读进度 API |
| `backend/app/api/notes.py` | 新增 | 笔记 API |
```

---

## MVP 优先实现顺序

### Phase 1：先把数据落点打好
1. Alembic 迁移：`books` hash 字段、`scan_jobs`、`scan_job_items`、`reading_progress.locator`、`book_notes`
2. 更新 ORM：`Book`、`ReadingProgress`、新增 `ScanJob` / `ScanJobItem` / `BookNote`
3. 补 schema：`reading.py`、`scanner.py`、`note.py`

**原因**：没有表结构和 schema，service / task 没有稳定边界。

### Phase 2：建立最小任务骨架
4. 新增 `celery_app.py`
5. 新增 `TaskDispatchService`
6. 新增 `FileAccessService`、`ScanJobService`
7. 改 `scanner.py`：`POST /scanner/jobs/directory`、`POST /scanner/jobs/file`、`GET /scanner/jobs*`

**原因**：先把“可追踪的后台任务”立起来，替换当前 `BackgroundTasks`。

### Phase 3：让扫描真正跑通
8. 重构 `scanner_service.py` 为 `ScanService`
9. 新增 `BookIngestService`
10. 实现 `scan.run_directory_job` / `scan.run_file_job` / `scan.process_scan_item`
11. 先按当前 path-based 规则完成第一版 persisted scan pipeline

**原因**：先解决“能跑 + 可观测”，再切换 hash 去重，降低风险。

### Phase 4：接入 hash 与内容去重
12. 新增 `HashService`
13. 实现 `hash.compute_book_hash`
14. 将主去重依据从 `file_path + file_size` 切到 `content_hash`
15. 在 `BookIngestService.apply_hash_result()` 内收口重复书合并逻辑

**原因**：这是 MVP 的关键能力，但复杂度高，放在 persisted pipeline 稳定后实现更安全。

### Phase 5：补搜索与用户侧同步 API
16. 新增 `BookSearchService`，把 `GET /books` 从 `ILIKE` 升级到 FTS + trigram
17. 新增 `ReadingProgressService` 与 `reading_progress.py`
18. 新增 `BookNoteService` 与 `notes.py`

**原因**：这些能力对前端价值高，但与扫描链路耦合较低，适合核心入库稳定后推进。

### Phase 6：补 enrich / maintenance
19. 扩展 `MetadataSyncService` 与 `CoverSyncService`
20. 为 metadata sync / cover sync 提供 worker 任务
21. 新增 `maintenance.reconcile_stalled_jobs`
22. 再优化 `files.py` 的 Range 支持与统一文件访问层

**原因**：这是稳定性与体验增强，不应阻塞核心入库主链。

---

## 风险与缓解

| 风险 | 缓解措施 |
|---|---|
| 保留 `books` 单文件模型后，hash 去重需要合并两条 `Book` 记录 | 把合并逻辑只收口到 `BookIngestService.apply_hash_result()`，一个事务内重绑 `reading_progress`、`book_notes`、`book_categories` |
| 每文件一个 Celery item task 可能造成消息很多 | root task 按批次 seed item，控制 worker 并发，先保守配置 |
| metadata provider 限流 / 脏数据 | 默认不在目录扫描里自动大批量外呼，MVP 先走管理员手动同步 |
| worker 崩溃后 item 卡在 `processing` | 增加 `maintenance.reconcile_stalled_jobs` 定时修复 |
| 搜索向量更新散落在多处导致数据不一致 | 强制所有书目 / 分类变更统一经过 `BookSearchService.refresh_document()` |
| Celery 状态与 API 展示不一致 | API 只读 PostgreSQL，不依赖 Celery result backend |

---

## 关键伪代码

### 1. 创建目录扫描任务

```python
def create_directory_scan_job(request, current_user, db):
    normalized = file_access.resolve_scan_root(request.directory)
    job = scan_job_service.create_job(
        job_type="scan_directory",
        requested_path=request.directory,
        normalized_path=normalized,
        created_by=current_user.id,
    )
    task_dispatcher.enqueue_scan_directory(job.id)
    return {"job_id": job.id, "status": "queued"}
```

### 2. 处理单个扫描项

```python
def process_scan_item(item_id):
    item = scan_job_service.claim_item(item_id)
    if not item:
        return

    snapshot = file_access.snapshot(item.file_path)
    metadata = local_metadata.extract(snapshot.path, snapshot.extension)
    result = scan_service.process_file(snapshot.path)

    search_service.refresh_document(result.book_id)
    scan_job_service.mark_item_finished(
        item.id,
        status=result.action,
        book_id=result.book_id,
    )

    if result.should_hash:
        task_dispatcher.enqueue_compute_hash(result.book_id, item_id=item.id)

    scan_job_service.maybe_finalize_job(item.job_id)
```

### 3. hash 写回与重复书合并

```python
def apply_hash_result(book_id, content_hash, algorithm, file_mtime, file_size):
    book = get_book_for_update(book_id)
    duplicate = find_book_by_content_hash(content_hash, exclude_id=book_id)

    if not duplicate:
        book.content_hash = content_hash
        book.hash_algorithm = algorithm
        book.hash_status = "done"
        book.file_mtime = file_mtime
        book.file_size = file_size
        return book.id

    canonical = choose_canonical_book(duplicate, book)
    merge_duplicate_books(source_book_id=book.id, target_book_id=canonical.id)

    canonical.content_hash = content_hash
    canonical.hash_algorithm = algorithm
    canonical.hash_status = "done"
    canonical.file_path = book.file_path
    canonical.file_mtime = file_mtime
    canonical.file_size = file_size
    return canonical.id
```

---

## SESSION_ID（供 `/ccg:execute` 使用）
- CODEX_SESSION: `019d2001-208c-73a1-a584-de96b71795a9`
- GEMINI_SESSION: `unavailable (capacity exhausted / HTTP 429)`
