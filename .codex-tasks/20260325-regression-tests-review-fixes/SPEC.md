# SPEC

## 任务
为本轮 review fixes 建立最小回归测试，并完成可执行验证。

## 形态
- single-full

## 范围
- `backend/app/api/books.py`
- `backend/app/schemas/reading.py`
- `backend/app/services/reading_service.py`
- `backend/app/services/book_ingest_service.py`
- `backend/app/services/scan_job_service.py`
- 新增最小测试文件，仅覆盖上述回归点

## 目标
1. 锁定 books create/update 的唯一约束冲突处理。
2. 锁定 reading schema / service 不再接受或写入 legacy `notes` / `bookmarks`。
3. 锁定 duplicate merge 字段集中维护。
4. 锁定 `retry_failed_items()` 在 0 failed item 时不漂移状态。

## 约束
- 先采用环境无关的最小自动化测试方式。
- 仅做与回归测试直接相关的最小代码调整。
- 每步后做最小验证并记录结果。