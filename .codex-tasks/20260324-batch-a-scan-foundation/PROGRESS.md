# PROGRESS

## 当前状态
- 任务: Batch A 任务化扫描骨架
- 形态: single-full
- 进度: 4/6
- 当前: 执行 Batch A 最小验证并补结果记录
- 文件: `.codex-tasks/20260324-batch-a-scan-foundation/TODO.csv`
- 下一步: 完成结果记录，向用户汇报 Batch A 已落地的代码与当前验证边界

## 已完成
- 已建立任务真相文件
- 已读取当前 `scanner.py`、`scanner_service.py`、`book.py`、`reading.py`、`config.py`、`requirements.txt`、`001_initial.py`、`router.py`、`schemas/__init__.py` 等基线文件
- 已确认当前扫描仍依赖 `BackgroundTasks`，且 `BookScanner` 负责目录遍历与入库
- 已新增 002 迁移、`scan_job.py`、`note.py`、`schemas/scanner.py`、`celery_app.py`、`tasks/__init__.py`
- 已新增 `FileAccessService`、`ScanJobService`、`TaskDispatchService`、`BookIngestService`
- 已将 `scanner_service.py` 收敛为 `ScanService.process_file()`
- 已将 `api/scanner.py` 改为 `/scanner/jobs/*` 主链路
- 已新增 `scan_tasks.py`，包含 root task / item task / retry task
- 已完成 py_compile 验证；import smoke 受当前环境缺少 `sqlalchemy` 影响未执行通过

## 关键发现
- `backend/app/api/scanner.py` 当前使用 `BackgroundTasks` 触发目录扫描
- `backend/app/services/scanner_service.py` 当前用 `file_path + file_size` 判断跳过
- `backend/app/db/base.py` 提供 `SessionLocal`，适合 task 内一任务一 session
- 当前还没有 `.codex-tasks/` 目录，需要本次任务自行创建

## Recovery
任务: Batch A 任务化扫描骨架
形态: single-full
进度: 6/6
当前: Batch A 已完成
文件: `.codex-tasks/20260324-batch-a-scan-foundation/TODO.csv`
下一步: 向用户汇报结果，并根据反馈继续 Batch B 或更新 llmdoc
