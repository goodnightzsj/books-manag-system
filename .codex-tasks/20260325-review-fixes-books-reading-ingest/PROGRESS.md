# PROGRESS

## 当前状态
- 任务: 顺序修复代码审查结论中的 books / reading / ingest 问题
- 形态: single-full
- 进度: 5/5
- 当前: 本轮审查修复已完成
- 文件: `.codex-tasks/20260325-review-fixes-books-reading-ingest/TODO.csv`
- 下一步: 向用户汇报修复结果并根据需要继续 commit

## 已完成
- 已读取 `backend/app/api/books.py`
- 已读取 `backend/app/services/reading_service.py`
- 已读取 `backend/app/schemas/reading.py`
- 已读取 `backend/app/services/book_ingest_service.py`
- 已确认 `books.isbn` 与 `books.file_path` 存在唯一约束来源于迁移
- 已完成 `backend/app/api/books.py` 唯一约束冲突处理，create/update 现在会返回稳定 409 而非裸 DB 异常
- 已完成 reading API 对 legacy `notes` / `bookmarks` 的移除，避免与 `book_notes` 形成双写语义
- 已完成 `backend/app/services/book_ingest_service.py` merge 字段定义收口，减少后续加字段时遗漏风险
- 已完成目标文件最小 `py_compile` 验证

## Recovery
任务: 顺序修复代码审查结论中的 books / reading / ingest 问题
形态: single-full
进度: 5/5
当前: 本轮审查修复已完成
文件: `.codex-tasks/20260325-review-fixes-books-reading-ingest/TODO.csv`
下一步: 向用户汇报修复结果并根据需要继续 commit
