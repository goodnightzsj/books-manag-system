# Books Platform MVP - 按文件实施清单

## 0. 目标

将已有的 MVP 规划拆成“按文件落地”的实施清单，便于后续按顺序执行。

约束：
- 仅覆盖后端 MVP
- 优先替换当前 `BackgroundTasks` 扫描链路为持久化 job + Celery
- 先打通扫描/入库/去重/搜索/阅读进度/笔记，再补 metadata/cover enrich
- 保持最小侵入，不在 MVP 引入 `book_files`

---

## 1. 推荐总顺序

1. 数据库迁移
2. ORM 模型
3. Pydantic Schema
4. Celery 与配置骨架
5. 扫描任务服务骨架
6. 扫描 API 改造
7. 扫描 item 处理链路
8. hash 与去重
9. 搜索升级
10. 阅读进度与笔记 API
11. metadata / cover 异步 enrich
12. 文件流与维护任务补强

---

## 2. Phase 1：数据库与模型层

### 2.1 `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py`（新增）
**目标**：一次性落下 MVP 所需表结构。

**实现项**：
- `books` 新增 `content_hash`、`hash_algorithm`、`hash_status`、`hash_error`、`file_mtime`、`source_provider`、`metadata_synced_at`、`search_vector`
- 为 `books` 增加 `content_hash`、`file_path`、`search_vector`、`title trgm`、`author trgm` 索引
- 创建 `scan_jobs`
- 创建 `scan_job_items`
- 为 `reading_progress` 新增 `locator`
- 为 `reading_progress` 增加 `(user_id, book_id)` 唯一约束
- 创建 `book_notes`
- 启用 `pg_trgm`

**前置检查**：
- 检查 `reading_progress` 是否存在 `(user_id, book_id)` 重复脏数据
- 确认 `books.file_path` 是否允许补唯一约束

---

### 2.2 `backend/app/models/book.py`（修改）
**目标**：让 `Book` 承载 hash / 搜索 / enrich 元数据。

**实现项**：
- 新增 `HashStatus` 枚举
- 为 `Book` 增加 hash 相关字段
- 增加 `file_mtime`、`source_provider`、`metadata_synced_at`
- 增加与 `BookNote` 的 relationship
- 视 ORM 策略决定是否显式声明 `search_vector`

**依赖**：迁移已完成。

---

### 2.3 `backend/app/models/reading.py`（修改）
**目标**：把阅读进度升级为多格式定位协议。

**实现项**：
- 新增 `locator` 字段（JSONB）
- 增加 `(user_id, book_id)` 唯一约束声明
- 保留 `notes` / `bookmarks` 作为 legacy 字段，不再作为主接口输出

---

### 2.4 `backend/app/models/scan_job.py`（新增）
**目标**：引入任务主表与任务明细表模型。

**实现项**：
- 定义 `ScanJobType`
- 定义 `ScanJobStatus`
- 定义 `ScanItemStatus`
- 定义 `ScanJob`
- 定义 `ScanJobItem`
- 配置 `items` relationship

---

### 2.5 `backend/app/models/note.py`（新增）
**目标**：独立承接“按书 / 按位置”的文本笔记。

**实现项**：
- 定义 `BookNote`
- 关联 `Book` / `User`
- 增加 `locator`、`note_text`、时间字段

---

### 2.6 `backend/app/models/__init__.py`（修改）
**目标**：补齐导出。

**实现项**：
- 导出 `ScanJob`
- 导出 `ScanJobItem`
- 导出 `BookNote`
- 若需要，也导出新枚举

---

## 3. Phase 2：Schema 层

### 3.1 `backend/app/schemas/reading.py`（新增）
**目标**：定义阅读进度请求/响应与 locator 联合类型。

**实现项**：
- `PdfLocator`
- `EpubLocator`
- `TxtLocator`
- `ReadingProgressUpdate`
- `ReadingProgressResponse`
- `RecentReadingItem`
- `RecentReadingList`

---

### 3.2 `backend/app/schemas/scanner.py`（新增）
**目标**：定义任务化扫描 API schema。

**实现项**：
- `ScanDirectoryRequest`
- `ScanFileRequest`
- `ScanJobCreatedResponse`
- `ScanJobResponse`
- `ScanJobListResponse`
- `ScanJobItemResponse`
- `ScanJobItemListResponse`

---

### 3.3 `backend/app/schemas/note.py`（新增）
**目标**：定义笔记 CRUD schema。

**实现项**：
- `BookNoteCreate`
- `BookNoteUpdate`
- `BookNoteResponse`
- `BookNoteListResponse`
- 与阅读进度保持同一套 locator 协议

---

### 3.4 `backend/app/schemas/book.py`（修改）
**目标**：补后台管理需要的图书字段输出。

**实现项**：
- 评估是否增加 `AdminBook`
- 让后台接口可选择暴露 `file_path`、`hash_status`、`content_hash`、`metadata_synced_at`
- 保持普通用户响应尽量不暴露本地路径

---

### 3.5 `backend/app/schemas/__init__.py`（修改）
**目标**：统一导出新增 schema。

**实现项**：
- 导出 reading / scanner / note 相关 schema
- 保持与现有 import 风格一致

---

## 4. Phase 3：配置与 Celery 骨架

### 4.1 `backend/app/core/config.py`（修改）
**目标**：增加任务队列和搜索相关配置。

**实现项**：
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`（可选）
- `CELERY_DEFAULT_QUEUE`
- `BOOKS_SCAN_QUEUE`
- `BOOKS_ENRICH_QUEUE`
- `BOOKS_MAINTENANCE_QUEUE`
- metadata provider 配置项（如 Google Books API key）
- 搜索相关开关 / 权重配置（如有必要）

---

### 4.2 `backend/app/celery_app.py`（新增）
**目标**：初始化 Celery app。

**实现项**：
- 创建 Celery 实例
- 配置 `scan` / `enrich` / `maintenance` 队列
- 注册 task 模块
- 配置 beat 定时任务入口（后续 maintenance 用）

---

### 4.3 `backend/app/tasks/__init__.py`（新增）
**目标**：统一导入任务模块。

**实现项**：
- 暴露 `scan_tasks`
- 暴露 `hash_tasks`
- 暴露 `metadata_tasks`
- 暴露 `cover_tasks`
- 暴露 `maintenance_tasks`

---

### 4.4 `backend/requirements.txt`（修改）
**目标**：补齐 Celery / Redis / 搜索 / 文件处理依赖。

**实现项**：
- 确认 `celery`
- 确认 `redis`
- 若封面/EPUB/PDF 处理依赖缺失则补齐
- 若使用 Postgres trigram/fts 只需 DB 扩展，无需额外 Python 包则不加

---

## 5. Phase 4：扫描基础服务骨架

### 5.1 `backend/app/services/file_access_service.py`（新增）
**目标**：统一处理路径安全和文件系统访问。

**实现项**：
- `resolve_scan_root()`：扫描根目录安全校验
- `resolve_book_file()`：读取/下载文件路径校验
- `iter_supported_files()`：遍历支持格式文件
- `snapshot()`：返回文件 size / mtime / ext / format
- `guess_media_type()`：给 files API 使用
- 为后续 Range 支持预留辅助方法

---

### 5.2 `backend/app/services/scan_job_service.py`（新增）
**目标**：统一管理 `scan_jobs` / `scan_job_items` 状态。

**实现项**：
- `create_job()`
- `claim_job()`
- `add_items()`
- `claim_item()`
- `mark_item_processing()`
- `mark_item_finished()`
- `maybe_finalize_job()`
- `retry_failed_items()`

**约束**：
- job / item 状态流转只能收口到这里

---

### 5.3 `backend/app/services/task_dispatch_service.py`（新增）
**目标**：统一 Celery 分发出口。

**实现项**：
- `enqueue_scan_directory()`
- `enqueue_scan_file()`
- `enqueue_process_scan_item()`
- `enqueue_retry_failed_items()`
- `enqueue_compute_hash()`
- `enqueue_metadata_sync()`
- `enqueue_cover_sync()`

**约束**：
- API / Service 不直接 `.delay()`

---

### 5.4 `backend/app/services/scanner_service.py`（修改）
**目标**：从“目录扫描大类”改为“单 item 扫描编排服务”。

**实现项**：
- 保留已有格式判断和本地 metadata 提取可复用部分
- 去掉目录遍历和 `BackgroundTasks` 耦合逻辑
- 收敛为 `ScanService.process_file()`
- 内部调用 `FileAccessService`、`LocalMetadataService`、`BookIngestService`、`BookSearchService`

---

### 5.5 `backend/app/services/book_ingest_service.py`（新增）
**目标**：统一图书创建/更新、hash 回写和重复书合并。

**实现项**：
- `upsert_scanned_book()`
- `apply_hash_result()`
- `merge_duplicate_books()`
- 统一维护 `indexed_at` / `updated_at`
- 处理重复书时重绑：`reading_progress`、`book_notes`、`book_categories`、`scan_job_items.book_id`

---

## 6. Phase 5：扫描任务实现

### 6.1 `backend/app/tasks/scan_tasks.py`（新增）
**目标**：实现 root scan task 与 item task。

**实现项**：
- `run_directory_job(job_id)`
- `run_file_job(job_id)`
- `process_scan_item(item_id)`
- `retry_failed_items(job_id)`
- 每个 task 内单独创建 DB session
- 认领失败时直接 no-op

---

### 6.2 `backend/app/api/scanner.py`（修改）
**目标**：把扫描入口改造成 job API。

**实现项**：
- 移除或兼容旧 `scan-directory` fire-and-forget 语义
- 新增 `POST /scanner/jobs/directory`
- 新增 `POST /scanner/jobs/file`
- 新增 `GET /scanner/jobs`
- 新增 `GET /scanner/jobs/{job_id}`
- 新增 `GET /scanner/jobs/{job_id}/items`
- 新增 `POST /scanner/jobs/{job_id}/retry-failed`
- 可选：`POST /scanner/books/{book_id}/metadata-sync`
- 可选：`POST /scanner/books/{book_id}/extract-cover`

**依赖**：
- `FileAccessService`
- `ScanJobService`
- `TaskDispatchService`

---

## 7. Phase 6：hash 与内容去重

### 7.1 `backend/app/services/hash_service.py`（新增）
**目标**：统一 hash 决策与计算。

**实现项**：
- `should_hash()`：基于 path / size / mtime / status 判断是否重算
- `compute_sha256()`
- quick fingerprint（可选）
- 错误归类

---

### 7.2 `backend/app/tasks/hash_tasks.py`（新增）
**目标**：异步执行 hash 计算与回写。

**实现项**：
- `compute_book_hash(book_id, item_id=None)`
- 失败时写回 `books.hash_status=failed`
- 如存在重复 `content_hash`，调用 `BookIngestService.apply_hash_result()` 合并
- 如存在 `item_id`，同步回填 `scan_job_items.detected_hash`

---

### 7.3 `backend/app/services/scanner_service.py`（二次修改）
**目标**：扫描链路接入 hash 分发。

**实现项**：
- `process_file()` 结果里返回 `should_hash`
- 让 `scan.process_scan_item` 在成功后按条件 enqueue hash task

---

## 8. Phase 7：搜索升级

### 8.1 `backend/app/services/search_service.py`（新增）
**目标**：收口全文检索与搜索向量刷新。

**实现项**：
- `search_books()`
- `refresh_document(book_id)`
- 统一 title / author / isbn / publisher / tags / category 搜索策略
- 实现排序与分页

---

### 8.2 `backend/app/api/books.py`（修改）
**目标**：把当前 `ILIKE` 搜索升级为 FTS + trigram。

**实现项**：
- 查询参数改为 `q`、`author`、`category_id`、`format`、`sort`、`order`
- 接入 `BookSearchService`
- 保留现有 CRUD
- 可选加入后台专用 metadata / cover 管理入口

---

## 9. Phase 8：阅读进度与笔记

### 9.1 `backend/app/services/reading_service.py`（新增）
**目标**：统一阅读进度查询与 upsert。

**实现项**：
- `get_for_user()`
- `upsert_for_user()`
- `list_recent_for_user()`
- 自动维护 `last_read_at`
- `progress_percent >= 100` 时自动推进 `status`

---

### 9.2 `backend/app/api/reading_progress.py`（新增）
**目标**：提供阅读进度 API。

**实现项**：
- `GET /reading-progress/{book_id}`
- `PUT /reading-progress/{book_id}`
- `GET /reading-progress/recent`

---

### 9.3 `backend/app/services/note_service.py`（新增）
**目标**：统一当前用户笔记 CRUD。

**实现项**：
- `list_for_book()`
- `create_for_book()`
- `update_note()`
- `delete_note()`
- 确保用户只能访问自己的笔记

---

### 9.4 `backend/app/api/notes.py`（新增）
**目标**：提供图书笔记 API。

**实现项**：
- `GET /books/{book_id}/notes`
- `POST /books/{book_id}/notes`
- `PUT /books/{book_id}/notes/{note_id}`
- `DELETE /books/{book_id}/notes/{note_id}`

---

## 10. Phase 9：metadata / cover enrich

### 10.1 `backend/app/services/metadata_service.py`（修改）
**目标**：拆成“本地提取 + 在线同步”双职责结构。

**实现项**：
- 保留 `MetadataExtractor` 作为本地提取器
- 增加 `MetadataSyncService`
- 统一 provider fallback 顺序
- 维护 `source_provider`、`metadata_synced_at`
- 同步完成后刷新搜索文档

---

### 10.2 `backend/app/tasks/metadata_tasks.py`（新增）
**目标**：异步执行元数据同步。

**实现项**：
- `sync_book_metadata(book_id, force=False, job_id=None)`
- provider 失败时不清空旧字段
- 需要时串联封面任务

---

### 10.3 `backend/app/services/cover_service.py`（修改）
**目标**：从工具类提升为封面同步服务。

**实现项**：
- 增加 `ensure_cover()`
- 支持“本地提取优先 / 远程下载优先”策略
- 封面已存在时允许 skip
- 为后续缩略图生成预留能力

---

### 10.4 `backend/app/tasks/cover_tasks.py`（新增）
**目标**：异步执行封面提取/下载。

**实现项**：
- `extract_or_download_cover(book_id, prefer_remote=False, source_url=None, force=False)`
- 不让封面失败影响图书主流程

---

## 11. Phase 10：文件服务与维护

### 11.1 `backend/app/api/files.py`（修改）
**目标**：改进流式阅读体验。

**实现项**：
- 统一通过 `FileAccessService.resolve_book_file()` 校验路径
- 为 `stream` 增加 `Range` 支持
- 必要时补 `HEAD /files/stream/{book_id}`
- 确保 PDF.js / EPUB 阅读侧可稳定读取

---

### 11.2 `backend/app/tasks/maintenance_tasks.py`（新增）
**目标**：修复 worker 崩溃后遗留状态。

**实现项**：
- `reconcile_stalled_jobs()`
- 识别卡在 `running` / `processing` 的 job/item
- 按策略标失败或重新排队

---

### 11.3 `backend/app/api/router.py`（修改）
**目标**：聚合新增 router。

**实现项**：
- 注册 `reading_progress.router`
- 注册 `notes.router`
- 保留现有 auth/books/scanner/categories/recommendations/files

---

## 12. 可选补充文件

### 12.1 `backend/app/main.py`（按需修改）
**何时需要改**：
- 若要补 startup 健康日志、Celery 相关初始化说明、统一异常处理时

**MVP 必须性**：低

---

### 12.2 `backend/entrypoint.sh`（按需修改）
**何时需要改**：
- 进入部署阶段，需要拆分 `api` / `worker` / `beat` 启动命令时

**MVP 必须性**：中

---

## 13. 最小可执行批次

### 批次 A：先把“能追踪的扫描任务”跑起来
- `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py`
- `backend/app/models/book.py`
- `backend/app/models/reading.py`
- `backend/app/models/scan_job.py`
- `backend/app/models/note.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/scanner.py`
- `backend/app/core/config.py`
- `backend/app/celery_app.py`
- `backend/app/services/file_access_service.py`
- `backend/app/services/scan_job_service.py`
- `backend/app/services/task_dispatch_service.py`
- `backend/app/services/scanner_service.py`
- `backend/app/services/book_ingest_service.py`
- `backend/app/tasks/scan_tasks.py`
- `backend/app/api/scanner.py`

### 批次 B：再接 hash 去重
- `backend/app/services/hash_service.py`
- `backend/app/tasks/hash_tasks.py`
- `backend/app/services/scanner_service.py`
- `backend/app/services/book_ingest_service.py`
- `backend/app/models/book.py`

### 批次 C：补搜索 + 用户侧接口
- `backend/app/services/search_service.py`
- `backend/app/api/books.py`
- `backend/app/schemas/reading.py`
- `backend/app/services/reading_service.py`
- `backend/app/api/reading_progress.py`
- `backend/app/schemas/note.py`
- `backend/app/services/note_service.py`
- `backend/app/api/notes.py`
- `backend/app/api/router.py`

### 批次 D：补 enrich + 文件体验
- `backend/app/services/metadata_service.py`
- `backend/app/tasks/metadata_tasks.py`
- `backend/app/services/cover_service.py`
- `backend/app/tasks/cover_tasks.py`
- `backend/app/api/files.py`
- `backend/app/tasks/maintenance_tasks.py`
- `backend/entrypoint.sh`

---

## 14. 结论

如果按这份文件清单执行，最稳妥的落地顺序是：
1. 先完成迁移 + 模型 + schema
2. 再完成 job 化扫描骨架
3. 再接 hash 去重
4. 再补搜索 / 阅读进度 / 笔记
5. 最后补 metadata / cover / Range / maintenance

这样能最大程度降低一次性改动过大的风险，并且每个批次都能形成可验证的中间里程碑。
