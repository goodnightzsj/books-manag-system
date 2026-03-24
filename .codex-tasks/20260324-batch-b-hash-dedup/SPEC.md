# SPEC

## 任务
Batch B：hash 去重与内容身份切换

## 形态
single-full

## 目标
在 Batch A 的任务化扫描基础上，引入内容 hash 计算与重复书合并能力，使系统从基于 `file_path + file_size` 的弱去重，升级为基于 `content_hash` 的内容身份判定。

## 本批范围
- 新增 `backend/app/services/hash_service.py`
- 新增 `backend/app/tasks/hash_tasks.py`
- 修改 `backend/app/services/book_ingest_service.py`
- 修改 `backend/app/services/task_dispatch_service.py`
- 修改 `backend/app/tasks/scan_tasks.py`
- 按需修改 `backend/app/services/scanner_service.py`
- 按需修改 `backend/app/tasks/__init__.py`

## 完成标准
- 新入库图书可异步计算 `content_hash`
- `books.hash_status` 在 `pending/done/failed/skipped` 间正确流转
- 相同内容、不同路径的文件可识别为重复
- 重复记录可在事务中完成合并，并重绑 `reading_progress`、`book_notes`、`book_categories`、`scan_job_items.book_id`
- `scan_job_items.detected_hash` 可按条件回填
- 主去重依据不再只是 `file_path + file_size`

## 非范围
- 不做 Batch C 的搜索、阅读进度、笔记 API
- 不做 Batch D 的 metadata/cover/file streaming/maintenance
- 不改 llmdoc，除非本批代码完成后用户再次要求

## 依赖
- Batch A 已完成，`scan_jobs` / `scan_job_items` 主链路可用
- 当前最小验证以静态/语法级和定向逻辑验证为主

## 关键风险
- 重复书合并会影响多张关联表
- hash 计算失败与扫描成功并存时，状态必须可接受且可恢复
- canonical book 选择规则必须稳定且集中在单一服务内
