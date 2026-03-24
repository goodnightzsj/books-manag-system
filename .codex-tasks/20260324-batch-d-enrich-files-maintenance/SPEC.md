# SPEC

## 任务
Batch D：metadata / cover enrich + 文件服务增强 + maintenance 任务

## 形态
single-full

## 目标
在 Batch A/B/C 已完成的扫描、内容身份、搜索与用户侧接口基础上，补齐后台 enrich 与文件体验能力：将单书 metadata 同步和封面提取/下载接入异步任务链路，增强文件流接口以支持 HTTP Range，并新增 maintenance task 修复 worker 崩溃后遗留的 stalled scan job / item，同时补足部署入口以支持 API / worker / beat 分工启动。

## 本批范围
- 新增 `backend/app/tasks/metadata_tasks.py`
- 新增 `backend/app/tasks/cover_tasks.py`
- 新增 `backend/app/tasks/maintenance_tasks.py`
- 修改 `backend/app/services/metadata_service.py`
- 修改 `backend/app/services/cover_service.py`
- 修改 `backend/app/services/task_dispatch_service.py`
- 修改 `backend/app/api/scanner.py`
- 修改 `backend/app/api/files.py`
- 修改 `backend/app/celery_app.py`
- 修改 `backend/app/core/config.py`
- 修改 `backend/app/tasks/__init__.py`
- 修改 `backend/entrypoint.sh`
- 仅在必要时读取并复用 `backend/app/services/file_access_service.py`、`backend/app/services/scan_job_service.py`、`backend/app/models/scan_job.py`

## 完成标准
- 管理员可触发单书 metadata 同步，且通过异步 task 分发执行
- metadata 同步失败不会清空已有 `Book` 字段，成功时会更新 `source_provider` / `metadata_synced_at` 并刷新搜索文档
- 图书封面可按策略执行本地提取或远程下载，并通过异步 task 触发
- `GET /api/v1/files/stream/{book_id}` 支持标准 `Range` 请求与 `206 Partial Content`
- worker 崩溃导致的 `running` / `processing` job/item 可被 maintenance task 识别并保守修复
- `entrypoint.sh` 可按角色支持 API / worker / beat 分工启动

## 非范围
- 不改 Batch A/B/C 已完成的扫描主流程、hash 去重逻辑、搜索/阅读/笔记接口语义
- 不新增前端页面或额外管理 UI
- 不做大规模集成测试或部署编排重构
- 不在本批主动更新 llmdoc，除非代码完成后用户再次要求

## 依赖
- Batch A 已完成，`scan_jobs` / `scan_job_items` / Celery 基础队列可用
- Batch B 已完成，图书内容身份与异步 hash 已稳定
- Batch C 已完成，搜索文档刷新能力已收口在 `BookSearchService`
- 当前验证以定向语法检查和必要的最小运行验证为主

## 关键风险
- 外部 metadata provider 失败或返回空字段时，不能覆盖已有有效数据
- 封面策略若分散在 router / task / service，容易出现重复判断与状态漂移
- Range 支持要保证边界正确，不能破坏现有下载/流式接口
- maintenance 自动修复必须保守，只处理明显 stalled 的 job/item，避免误判正在执行的任务
