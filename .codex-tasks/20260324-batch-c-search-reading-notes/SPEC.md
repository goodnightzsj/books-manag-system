# SPEC

## 任务
Batch C：搜索升级 + 阅读进度 + 笔记 API

## 形态
single-full

## 目标
在 Batch A/B 已完成的扫描与内容身份基础上，补齐用户侧 MVP 能力：图书搜索升级为 PostgreSQL FTS + trigram，新增阅读进度 locator 协议与用户隔离的阅读进度 API，并新增独立 `book_notes` CRUD API。

## 本批范围
- 新增 `backend/app/services/search_service.py`
- 新增 `backend/app/schemas/reading.py`
- 新增 `backend/app/services/reading_service.py`
- 新增 `backend/app/api/reading_progress.py`
- 新增 `backend/app/schemas/note.py`
- 新增 `backend/app/services/note_service.py`
- 新增 `backend/app/api/notes.py`
- 修改 `backend/app/api/books.py`
- 修改 `backend/app/schemas/book.py`
- 修改 `backend/app/schemas/__init__.py`
- 修改 `backend/app/api/router.py`
- 按需修改 `backend/app/models/reading.py`
- 按需修改 `backend/app/models/note.py`

## 完成标准
- `GET /api/v1/books` 支持 `q`、过滤、排序、分页，不再只依赖 `ILIKE`
- 搜索逻辑集中到独立 service，并覆盖 title / author / isbn / publisher / tags / category 维度
- `GET /api/v1/reading-progress/{book_id}` 可查询当前用户阅读进度
- `PUT /api/v1/reading-progress/{book_id}` 可创建或更新当前用户阅读进度
- `GET /api/v1/reading-progress/recent` 可返回最近阅读列表
- `GET/POST/PUT/DELETE /api/v1/books/{book_id}/notes...` 可用
- locator 协议可表达 PDF / EPUB / TXT 阅读位置
- 用户只能访问自己的阅读进度与笔记

## 非范围
- 不做 Batch D 的 metadata / cover / files / maintenance 改动
- 不改扫描/hash 主链路
- 不改 llmdoc，除非本批代码完成后用户再次要求

## 依赖
- Batch A 已完成，图书与扫描主链稳定
- Batch B 已完成，`content_hash` 去重链路已接通
- 当前最小验证以静态/语法级与定向接口/服务验证为主

## 关键风险
- 搜索 SQL 与排序/分页组合容易退化为多处分散逻辑
- `reading_progress` 的 locator 协议必须稳定且面向多格式
- 旧 `reading_progress.notes/bookmarks` 与新 `book_notes` 需要明确边界
- 读写接口必须严格按当前用户隔离，不能默认管理员越权
