# PROGRESS

## 当前状态
- 任务: 提交后的收尾工作，先同步 review fixes 的最小 llmdoc
- 形态: single-full
- 进度: 3/3
- 当前: 第 1 步已完成，准备进入回归测试
- 文件: `.codex-tasks/20260325-post-commit-doc-test-validation/TODO.csv`
- 下一步: 建立回归测试任务，优先覆盖 books 唯一冲突、reading legacy 字段、duplicate merge、retry_failed_items

## 已完成
- 已确认前一轮实现与 review fixes 已提交到 `0f94bde`
- 已读取目标 llmdoc 文件与本轮 review fixes 对应源码
- 已更新 `llmdoc/reference/api-endpoints.md`，补充 books create/update 唯一冲突返回 `409 Conflict`
- 已更新 `llmdoc/reference/schemas-reference.md`，补充 `ReadingProgressUpdate` 不再暴露 legacy `notes` / `bookmarks`
- 已更新 `llmdoc/architecture/services-architecture.md`，补充 `ReadingProgressService` 停止写 legacy 字段与 `BookIngestService.MERGEABLE_BOOK_FIELDS` 收口
- 已完成最小验证：`python -m py_compile backend/app/api/books.py backend/app/schemas/reading.py backend/app/services/reading_service.py backend/app/services/book_ingest_service.py`

## Recovery
任务: 提交后的收尾工作，先同步 review fixes 的最小 llmdoc
形态: single-full
进度: 3/3
当前: 第 1 步已完成，准备进入回归测试
文件: `.codex-tasks/20260325-post-commit-doc-test-validation/TODO.csv`
下一步: 建立回归测试任务，优先覆盖 books 唯一冲突、reading legacy 字段、duplicate merge、retry_failed_items
