# Books Platform MVP - 按批次可直接执行的开发任务单

## 0. 说明

本清单基于以下规划文档汇总而成：
- `.claude/plan/books-platform-mvp-file-checklist.md`
- `.claude/plan/books-platform-mvp-services-celery.md`
- `.claude/plan/books-platform-mvp-orm-routes.md`
- `.claude/plan/books-platform-mvp-migration-schema.md`
- `.claude/plan/books-platform-mvp-schema-api.md`

目标：把 MVP 后端实施拆成 4 个可独立推进、可验证交付的开发批次。

原则：
- 先打通数据结构与任务骨架，再接核心业务链路
- 先解决“可观测 + 可追踪 + 可重试”，再切主去重逻辑
- 每批都应有明确完成标准，避免只完成一半接口或半套模型
- 当前仅做执行计划，不修改产品代码

---

# Batch A：任务化扫描骨架落地

## 1. 目标

建立 MVP 的基础底座，让当前 `BackgroundTasks` 扫描模式升级为：
- 有持久化 `scan_jobs` / `scan_job_items`
- 有 Celery 任务分发骨架
- 有扫描 API 创建/查询能力
- 有最小可运行的单 item 处理链路

本批次结束后，系统应具备“创建扫描任务 → 后台消费 → 查询任务进度”的能力，即使 hash 去重和搜索升级还未接入完全。

---

## 2. 涉及文件

### 新增
- `backend/alembic/versions/002_mvp_scan_hash_reading_notes.py`
- `backend/app/models/scan_job.py`
- `backend/app/models/note.py`
- `backend/app/schemas/scanner.py`
- `backend/app/celery_app.py`
- `backend/app/tasks/__init__.py`
- `backend/app/services/file_access_service.py`
- `backend/app/services/scan_job_service.py`
- `backend/app/services/task_dispatch_service.py`
- `backend/app/services/book_ingest_service.py`
- `backend/app/tasks/scan_tasks.py`

### 修改
- `backend/app/models/book.py`
- `backend/app/models/reading.py`
- `backend/app/models/__init__.py`
- `backend/app/core/config.py`
- `backend/app/services/scanner_service.py`
- `backend/app/api/scanner.py`
- `backend/requirements.txt`

---

## 3. 执行顺序

1. 迁移文件落库
   - 先写 `002_mvp_scan_hash_reading_notes.py`
   - 先确保 `scan_jobs`、`scan_job_items`、`book_notes`、`reading_progress.locator` 可落地

2. 更新 ORM 模型
   - `book.py`
   - `reading.py`
   - `scan_job.py`
   - `note.py`
   - `models/__init__.py`

3. 补扫描 schema
   - 完成 `schemas/scanner.py`

4. 建 Celery/配置骨架
   - `config.py`
   - `celery_app.py`
   - `tasks/__init__.py`
   - `requirements.txt`

5. 建基础服务
   - `file_access_service.py`
   - `scan_job_service.py`
   - `task_dispatch_service.py`
   - `book_ingest_service.py`
   - 将 `scanner_service.py` 收敛为单 item 编排

6. 落扫描任务
   - `tasks/scan_tasks.py`
   - `api/scanner.py`

7. 联调验证
   - 管理员可创建目录/单文件任务
   - 任务状态可查询
   - 至少一类支持格式文件能被入库并关联到 `scan_job_items`

---

## 4. 完成标准

满足以下条件才算 Batch A 完成：
- `POST /api/v1/scanner/jobs/directory` 可创建任务
- `POST /api/v1/scanner/jobs/file` 可创建任务
- `GET /api/v1/scanner/jobs/{job_id}` 可返回任务状态
- `GET /api/v1/scanner/jobs/{job_id}/items` 可返回明细
- worker 能消费 scan task 并写回 `scan_jobs` / `scan_job_items`
- 扫描处理链路至少能完成：路径校验 → 文件发现 → item 创建 → item 处理 → Book upsert
- 不再依赖 `backend/app/api/scanner.py` 中旧的 `BackgroundTasks` 作为主链路

---

## 5. 依赖关系

- 无外部批次依赖，这是整个 MVP 的起始批次
- 但依赖 PostgreSQL / Redis 环境可用
- 依赖当前 `backend/app/db` 与 Session 创建方式保持兼容

---

## 6. 主要风险

- **风险 1：迁移一次性改动较多**
  - 缓解：先保证任务表和关键字段可落地，再逐步接业务

- **风险 2：`scanner_service.py` 当前职责过重**
  - 缓解：本批只做最小收敛，不一次性重写所有逻辑

- **风险 3：Celery 集成后 API/worker 会话边界不清**
  - 缓解：强制一 task 一 session，router 不向 task 传 session

- **风险 4：旧扫描接口兼容问题**
  - 缓解：MVP 优先新接口，旧接口可短期转发或直接废弃

---

# Batch B：hash 去重与内容身份切换

## 1. 目标

把当前基于 `file_path + file_size` 的弱去重，升级为：
- `content_hash` 作为主去重依据
- hash 计算异步化
- 重复书合并逻辑事务化
- 扫描结果与 hash 状态联动

本批次结束后，系统应真正具备“内容身份”能力，而不是仅凭路径判断重复。

---

## 2. 涉及文件

### 新增
- `backend/app/services/hash_service.py`
- `backend/app/tasks/hash_tasks.py`

### 修改
- `backend/app/models/book.py`
- `backend/app/services/scanner_service.py`
- `backend/app/services/book_ingest_service.py`
- `backend/app/services/task_dispatch_service.py`
- `backend/app/tasks/scan_tasks.py`

---

## 3. 执行顺序

1. 定义 hash service
   - `should_hash()`
   - `compute_sha256()`
   - 错误分类与状态回写策略

2. 在 `book_ingest_service.py` 中实现
   - `apply_hash_result()`
   - `merge_duplicate_books()`

3. 新增 `hash_tasks.py`
   - 支持 `compute_book_hash(book_id, item_id=None)`

4. 修改扫描链路
   - `scan_tasks.py` 在 item 成功后按条件分发 hash task
   - `scanner_service.py` 返回 `should_hash`
   - `task_dispatch_service.py` 统一发 hash 任务

5. 联调重复书合并逻辑
   - hash 命中重复内容时，选择 canonical book
   - 迁移并重绑关联关系

---

## 4. 完成标准

满足以下条件才算 Batch B 完成：
- 新入库图书可异步计算 `content_hash`
- `books.hash_status` 会在 `pending/done/failed/skipped` 间正确流转
- 相同内容、不同路径的文件会被识别为重复
- 重复记录可在事务内完成合并，不残留脏引用
- `scan_job_items.detected_hash` 可按条件回填
- 主去重依据不再是单纯的 `file_path + file_size`

---

## 5. 依赖关系

- 强依赖 Batch A 完成
- 依赖 `scan_jobs` / `scan_job_items` 已可稳定运行
- 依赖 `BookIngestService` 已具备基本 upsert 能力

---

## 6. 主要风险

- **风险 1：重复书合并会影响多张关联表**
  - 缓解：所有重绑只允许在 `BookIngestService.merge_duplicate_books()` 内完成

- **风险 2：hash 计算开销高**
  - 缓解：worker 异步执行，按 size/mtime 决定是否跳过重算

- **风险 3：合并策略不稳定导致 canonical 选择混乱**
  - 缓解：先固定选择规则，避免多处隐式判断

- **风险 4：扫描成功但 hash 失败造成状态不一致**
  - 缓解：明确“Book 已创建但 hash 失败”是允许状态，只写 `hash_error`

---

# Batch C：搜索升级 + 阅读进度 + 笔记 API

## 1. 目标

把用户侧 MVP 能力补齐：
- 图书搜索从 `ILIKE` 升级到 PostgreSQL FTS + trigram
- 阅读进度支持统一 locator
- 笔记从粗粒度字段升级为独立 `book_notes`
- 提供面向 Web/多端阅读器的基础同步接口

本批次结束后，用户侧最核心的“找书、继续阅读、记笔记”能力应可用。

---

## 2. 涉及文件

### 新增
- `backend/app/services/search_service.py`
- `backend/app/schemas/reading.py`
- `backend/app/services/reading_service.py`
- `backend/app/api/reading_progress.py`
- `backend/app/schemas/note.py`
- `backend/app/services/note_service.py`
- `backend/app/api/notes.py`

### 修改
- `backend/app/api/books.py`
- `backend/app/schemas/book.py`
- `backend/app/schemas/__init__.py`
- `backend/app/api/router.py`
- `backend/app/models/reading.py`
- `backend/app/models/note.py`

---

## 3. 执行顺序

1. 先做搜索服务
   - 新建 `search_service.py`
   - 定义搜索、排序、分页、文档刷新方法

2. 改 `api/books.py`
   - 从 `search`/`ILIKE` 切到 `q + filters + sort`
   - 接入 `BookSearchService`

3. 新增阅读进度 schema + service + router
   - `schemas/reading.py`
   - `services/reading_service.py`
   - `api/reading_progress.py`

4. 新增笔记 schema + service + router
   - `schemas/note.py`
   - `services/note_service.py`
   - `api/notes.py`

5. 更新导出与路由聚合
   - `schemas/__init__.py`
   - `api/router.py`

6. 联调用户链路
   - 搜索列表
   - 获取/更新阅读进度
   - 笔记 CRUD

---

## 4. 完成标准

满足以下条件才算 Batch C 完成：
- `GET /api/v1/books` 支持全文检索、过滤、排序、分页
- 搜索不再仅依赖 `ILIKE`
- `GET/PUT /api/v1/reading-progress/{book_id}` 可用
- `GET /api/v1/reading-progress/recent` 可返回最近阅读
- `GET/POST/PUT/DELETE /api/v1/books/{book_id}/notes` 可用
- locator 协议可表达 PDF/EPUB/TXT 三类阅读位置
- 用户只能访问自己的阅读进度与笔记

---

## 5. 依赖关系

- 依赖 Batch A 完成
- 建议在 Batch B 之后执行，因为搜索与阅读页更依赖稳定的 `Book` 记录
- 其中阅读进度/笔记本身不强依赖 hash 去重，但依赖模型/迁移已落地

---

## 6. 主要风险

- **风险 1：搜索向量刷新点过多，容易漏更新**
  - 缓解：统一通过 `BookSearchService.refresh_document()` 收口

- **风险 2：阅读 locator 结构在多格式下不一致**
  - 缓解：提前固定三类 locator 协议，不做开放式结构

- **风险 3：旧 `reading_progress.notes/bookmarks` 与新 `book_notes` 语义冲突**
  - 缓解：新接口只认 `book_notes`，旧字段保留但不继续扩展

- **风险 4：权限边界不清**
  - 缓解：note / reading API 一律按当前用户隔离，不给管理员默认越权查看

---

# Batch D：metadata / cover enrich + 文件服务增强 + 维护任务

## 1. 目标

在核心链路稳定后补足体验和稳定性能力：
- 在线 metadata 同步
- 封面提取 / 下载
- 文件流式接口增强，支持 Range
- maintenance 任务修复 stalled jobs
- 为后续 Admin Web / Reader Web 打好体验基础

本批次结束后，系统应具备更完整的后台运维能力和更好的文件阅读体验。

---

## 2. 涉及文件

### 新增
- `backend/app/tasks/metadata_tasks.py`
- `backend/app/tasks/cover_tasks.py`
- `backend/app/tasks/maintenance_tasks.py`

### 修改
- `backend/app/services/metadata_service.py`
- `backend/app/services/cover_service.py`
- `backend/app/services/task_dispatch_service.py`
- `backend/app/api/scanner.py`
- `backend/app/api/files.py`
- `backend/app/celery_app.py`
- `backend/app/core/config.py`
- `backend/entrypoint.sh`

---

## 3. 执行顺序

1. 扩展 `metadata_service.py`
   - 增加 `MetadataSyncService`
   - 定义 provider fallback 与字段合并策略

2. 新增 `metadata_tasks.py`
   - 支持单书 metadata sync

3. 扩展 `cover_service.py`
   - 增加 `ensure_cover()`
   - 支持本地提取 / 远程下载策略

4. 新增 `cover_tasks.py`
   - 支持封面异步提取/下载

5. 补 scanner 管理动作
   - `POST /scanner/books/{book_id}/metadata-sync`
   - `POST /scanner/books/{book_id}/extract-cover`

6. 增强 `api/files.py`
   - 统一走 `FileAccessService`
   - 增加 `Range` 支持

7. 新增 `maintenance_tasks.py`
   - 定时修复卡住的 job/item

8. 视部署方式补 `entrypoint.sh`
   - 拆 worker / beat / api 进程启动方式

---

## 4. 完成标准

满足以下条件才算 Batch D 完成：
- 管理员可触发单书 metadata 同步
- metadata 同步失败不会清空现有书目字段
- 图书可按策略提取或下载封面
- `GET /api/v1/files/stream/{book_id}` 支持 Range 请求
- worker 崩溃导致的卡住任务可被 maintenance task 识别并修复
- `entrypoint.sh` 或部署脚本可支持 API / worker / beat 分工启动

---

## 5. 依赖关系

- 强依赖 Batch A 完成
- 建议在 Batch B/C 完成后再做
- 文件流增强可独立推进，但 metadata/cover 最好在图书主链稳定后进行

---

## 6. 主要风险

- **风险 1：外部 metadata provider 不稳定或限流**
  - 缓解：默认手动触发，失败保留旧数据

- **风险 2：封面策略复杂度失控**
  - 缓解：MVP 只做“本地提取 + 远程下载”两类路径，不做多级缓存体系

- **风险 3：Range 支持改动可能影响现有文件下载逻辑**
  - 缓解：下载与流式分开验证，先保证流式稳定

- **风险 4：maintenance 自动修复可能误判状态**
  - 缓解：先只处理明显超时的 `running/processing` 项，策略保守

---

# 最终依赖图

- Batch A：起始批次，必须先做
- Batch B：依赖 A
- Batch C：依赖 A，建议排在 B 之后
- Batch D：依赖 A，建议排在 B/C 之后

推荐顺序：
1. Batch A
2. Batch B
3. Batch C
4. Batch D

---

# 交付建议

如果按开发节奏推进，建议采用以下验收方式：
- 每完成一个 Batch，就冻结一次 API/模型边界
- 每个 Batch 至少补一轮最小可验证测试
- 不跨 Batch 混做，以免 job/hash/search/reader 状态同时漂移

这样可以把整条 MVP 路线拆成 4 个明确里程碑，而不是一次性推全量改造。
