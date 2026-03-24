# PROGRESS

## 当前状态
- 任务: Batch D metadata / cover enrich + 文件服务增强 + maintenance 任务
- 形态: single-full
- 进度: 7/7
- 当前: Batch D 已完成
- 文件: `.codex-tasks/20260324-batch-d-enrich-files-maintenance/TODO.csv`
- 下一步: 向用户汇报 Batch D 结果，并根据反馈决定是否更新 llmdoc

## 已完成
- 已读取 `.claude/plan/books-platform-mvp-batch-task-list.md` 与 `.claude/plan/books-platform-mvp-file-checklist.md`
- 已读取相关 llmdoc：`llmdoc/index.md`、`llmdoc/architecture/services-architecture.md`、`llmdoc/guides/scanning-workflow.md`、`llmdoc/reference/config-reference.md`
- 已建立 Batch D 任务目录、SPEC、TODO、PROGRESS
- 已读取 `backend/app/services/metadata_service.py`、`backend/app/services/cover_service.py`、`backend/app/services/task_dispatch_service.py`、`backend/app/api/scanner.py`、`backend/app/api/files.py`、`backend/app/celery_app.py`、`backend/app/core/config.py`、`backend/app/tasks/__init__.py`、`backend/entrypoint.sh`
- 已补读 `backend/app/services/file_access_service.py`、`backend/app/services/scan_job_service.py`、`backend/app/tasks/scan_tasks.py`、`backend/app/tasks/hash_tasks.py`、`backend/app/models/scan_job.py`、`backend/app/models/book.py`、`backend/app/services/search_service.py`、`backend/app/db/base.py`
- 已新增 `MetadataSyncService` 与 `metadata.sync_book_metadata`，metadata 成功后会刷新 `search_vector` 并串联 cover task
- 已新增 `CoverService.ensure_cover()` 与 `cover.extract_or_download_cover`，支持本地优先或远程优先策略
- 已把 scanner 的 metadata / cover 管理入口改为异步排队模式
- 已增强 `files/stream` 支持 Range、206、HEAD，并统一复用 `FileAccessService`
- 已新增 `maintenance.reconcile_stalled_jobs`，并在 Celery beat 中注册定时调和任务
- 已调整 `entrypoint.sh`，支持 `APP_ROLE=api|worker|beat`
- 已完成 Batch D 核心文件 `py_compile` 最小验证

## 关键发现
- 原有 metadata sync / cover extract 都在 `backend/app/api/scanner.py` 同步执行，最小安全改造是把 router 改成纯排队入口，把实际合并/封面策略收口到 task + service
- `BookSearchService.refresh_document()` 已存在，因此 metadata 同步完成后可以直接刷新 `search_vector`，无需再补迁移或分散刷新逻辑
- `FileAccessService` 已具备路径限制与 MIME 推断能力，适合直接复用到 `files` 下载/流式接口，避免再次手写文件路径校验
- maintenance 修复应保守：当前只处理明显超时的 `processing` item 与长期无 item 的 `running` job，并对已处理完但未闭合的 job 调用 `maybe_finalize_job()` 收敛状态

## Recovery
任务: Batch D metadata / cover enrich + 文件服务增强 + maintenance 任务
形态: single-full
进度: 7/7
当前: Batch D 已完成
文件: `.codex-tasks/20260324-batch-d-enrich-files-maintenance/TODO.csv`
下一步: 向用户汇报 Batch D 结果，并根据反馈决定是否更新 llmdoc
