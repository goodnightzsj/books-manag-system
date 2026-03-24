# Batch A - 任务化扫描骨架

## 目标

只实现 Batch A：把当前基于 `BackgroundTasks` 的扫描入口升级为持久化 job + Celery 骨架，支持管理员创建目录/单文件扫描任务、查询任务与任务明细，并让 worker 能处理扫描项并完成最小图书入库。

## 范围

### 包含
- Alembic 迁移：`books` 扩展字段、`scan_jobs`、`scan_job_items`、`reading_progress.locator`、`book_notes`
- ORM：`Book`、`ReadingProgress`、`ScanJob`、`ScanJobItem`、`BookNote`
- Schema：`scanner.py`
- Celery/config/task 骨架
- `FileAccessService`
- `ScanJobService`
- `TaskDispatchService`
- `BookIngestService`
- `ScanService`
- `scan_tasks.py`
- `api/scanner.py` job 化

### 不包含
- Hash 计算与重复书合并执行链路
- 搜索升级
- 阅读进度 API
- 笔记 API
- metadata/cover 异步任务
- files Range 支持

## 完成标准
- `POST /api/v1/scanner/jobs/directory`
- `POST /api/v1/scanner/jobs/file`
- `GET /api/v1/scanner/jobs`
- `GET /api/v1/scanner/jobs/{job_id}`
- `GET /api/v1/scanner/jobs/{job_id}/items`
- `POST /api/v1/scanner/jobs/{job_id}/retry-failed`
- worker 可消费扫描任务并回写 `scan_jobs` / `scan_job_items`
- 扫描项可调用本地 metadata 提取并完成 `Book` upsert

## 风险
- 迁移一次性改动较多
- 旧 `scanner.py` 职责很重
- Celery/DB session 边界容易出错
- 单文件与目录扫描要统一进入 job 模型
