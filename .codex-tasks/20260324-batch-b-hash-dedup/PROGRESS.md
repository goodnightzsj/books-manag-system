# PROGRESS

## 当前状态
- 任务: Batch B hash 去重与内容身份切换
- 形态: single-full
- 进度: 6/6
- 当前: Batch B 已完成
- 文件: `.codex-tasks/20260324-batch-b-hash-dedup/TODO.csv`
- 下一步: 向用户汇报 Batch B 结果，并根据反馈决定是否更新 llmdoc 或继续 Batch C

## 已完成
- 已读取 Batch B 计划文档与当前 llmdoc 相关部分
- 已建立 Batch B 任务目录、SPEC、TODO、PROGRESS
- 已读取 `book_ingest_service.py`、`scan_tasks.py`、`task_dispatch_service.py`、`scanner_service.py`、`tasks/__init__.py`、`book.py`、`reading.py`、`note.py`、`scan_job.py` 现状
- 已新增 `backend/app/services/hash_service.py`，提供 `should_hash()`、`compute_sha256()`、错误分类
- 已新增 `backend/app/tasks/hash_tasks.py`，提供 `compute_book_hash(book_id, item_id=None)`
- 已在 `backend/app/services/book_ingest_service.py` 中实现 `apply_hash_result()`、`merge_duplicate_books()` 与 canonical 规则
- 已把 `reading_progress`、`book_notes`、`book_categories`、`scan_job_items.book_id` 纳入重复书合并重绑
- 已将 `TaskDispatchService` 改为统一通过 `celery_app.send_task()` 分发 scan/hash 任务
- 已修改 `scan_tasks.py`，root/item/retry 链路统一走 dispatch service，并在 item 成功后按条件分发 hash 任务
- 已更新 `backend/app/tasks/__init__.py` 与 `backend/app/celery_app.py` 注册 hash task
- 已完成 `py_compile` 最小验证

## 关键发现
- 当前 `BookIngestService.upsert_scanned_book()` 已不再让 `should_hash` 恒为 `False`；是否重算由 `HashService.should_hash()` 基于 path/size/mtime/status 决策
- 内容身份已切到 `content_hash` 链路：hash 任务完成后会调用 `apply_hash_result()`，并在发现重复内容时触发事务内合并
- `scan_job_items.detected_hash` 已在 hash 任务中回填
- canonical book 当前固定按 `created_at` 最早、再按 `id` 排序选择，避免多处隐式判断
- 运行时验证仍以静态/语法级为主，尚未补全依赖环境下的集成 smoke
- 实现过程中修复了一处运行时问题：`BookIngestService._is_empty()` 不能用包含 list/dict 的 set 判空，已改为类型化判断

## Recovery
任务: Batch B hash 去重与内容身份切换
形态: single-full
进度: 6/6
当前: Batch B 已完成
文件: `.codex-tasks/20260324-batch-b-hash-dedup/TODO.csv`
下一步: 向用户汇报 Batch B 结果，并根据反馈决定是否更新 llmdoc 或继续 Batch C
