# PROGRESS

## 当前状态
- 任务: Batch C 搜索升级 + 阅读进度 + 笔记 API
- 形态: single-full
- 进度: 6/6
- 当前: Batch C 已完成
- 文件: `.codex-tasks/20260324-batch-c-search-reading-notes/TODO.csv`
- 下一步: 向用户汇报 Batch C 结果，并根据反馈决定是否更新 llmdoc 或继续 Batch D

## 已完成
- 已读取 `.claude/plan/books-platform-mvp-batch-task-list.md` 与 `.claude/plan/books-platform-mvp-file-checklist.md`
- 已读取 `backend/app/api/books.py`、`backend/app/api/router.py`、`backend/app/models/reading.py`、`backend/app/models/note.py`、`backend/app/schemas/book.py`、`backend/app/schemas/__init__.py`、`backend/app/models/book.py`、`backend/app/models/user.py`、`backend/app/api/deps.py`、`backend/app/schemas/user.py`、`backend/app/api/categories.py`
- 已读取相关 llmdoc：`llmdoc/architecture/api-architecture.md`、`llmdoc/reference/schemas-reference.md`
- 已建立 Batch C 任务目录、SPEC、TODO、PROGRESS
- 已新增 `backend/app/services/search_service.py`，收口 FTS + trigram 搜索、过滤、排序与分页
- 已改造 `backend/app/api/books.py`，将列表接口切到 `q` / `author` / `category_id` / `format` / `sort` / `order`
- 已更新 `backend/app/schemas/book.py`，让 `file_format` / `hash_status` / `metadata_synced_at` 进入响应并用枚举类型约束输入输出
- 已新增 `backend/app/schemas/reading.py`、`backend/app/services/reading_service.py`、`backend/app/api/reading_progress.py`
- 已新增 `backend/app/schemas/note.py`、`backend/app/services/note_service.py`、`backend/app/api/notes.py`
- 已更新 `backend/app/schemas/__init__.py` 与 `backend/app/api/router.py`，接入 reading/note schema 导出与新路由
- 已完成 `py_compile` 最小验证

## 关键发现
- 当前搜索升级可以直接复用 `books.search_vector`、title/author trigram 索引与 `book_categories` 关联表，无需再做迁移
- 为避免把搜索逻辑散落在 router 中，`GET /books` 已收口到 `BookSearchService.search_books()`
- `reading_progress` 已有 `locator` 字段和 `(user_id, book_id)` 唯一约束，适合直接做“按用户 upsert”接口
- `book_notes` 模型已存在，且 `user_id` / `book_id` 足够支持用户隔离 CRUD
- 用户侧接口不应默认给管理员越权读写；本批实现统一只按 `current_user.id` 访问阅读进度与笔记
- 当前最小验证仍以静态/语法级为主，尚未补全依赖数据库环境的接口级 smoke

## Recovery
任务: Batch C 搜索升级 + 阅读进度 + 笔记 API
形态: single-full
进度: 6/6
当前: Batch C 已完成
文件: `.codex-tasks/20260324-batch-c-search-reading-notes/TODO.csv`
下一步: 向用户汇报 Batch C 结果，并根据反馈决定是否更新 llmdoc 或继续 Batch D
