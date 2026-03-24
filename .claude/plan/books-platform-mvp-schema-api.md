# Books Platform MVP Schema Draft + API List

## 0. 设计前提（MVP 范围收敛）

为了让 MVP 尽快落地，本稿采用 **最小迁移原则**：

1. **保留当前 `books` 单文件模型**，不在 MVP 就引入 `book_files`
   - 当前代码已把 `file_path` / `file_format` / `file_size` 放在 `Book` 上：`backend/app/models/book.py:25-52`
   - MVP 先在 `books` 上补 `content_hash` 和搜索字段，降低改造成本
   - 如果后续明确需要“一书多文件 / 多副本 / 多格式归一”，再在 Phase 2 拆 `book_files`

2. **MVP 支持基础做笔记，但不做高亮/书签复杂模型**
   - 当前 `ReadingProgress.notes` / `bookmarks` 过粗：`backend/app/models/reading.py:23-31`
   - MVP 改为独立 `book_notes` 表，支持“按书 / 按位置”的纯文本笔记
   - `annotations` / `bookmarks` 留到 Phase 2

3. **搜索先走 PostgreSQL FTS**
   - 当前 `GET /books` 仍是 `ILIKE`：`backend/app/api/books.py:25-32`
   - MVP 先升级为 `tsvector + pg_trgm`

4. **扫描必须 job 化**
   - 当前 `scan-directory` 只用 `BackgroundTasks`：`backend/app/api/scanner.py:42-56`
   - MVP 改为持久化 job + worker

---

## 1. MVP 表结构草案

## 1.1 `users`（沿用现有）

> 来源：`backend/app/models/user.py:15-30`

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 用户 ID |
| username | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| display_name | VARCHAR(128) | NULL | 显示名 |
| avatar_url | TEXT | NULL | 头像 |
| role | ENUM(admin,user) | NOT NULL, DEFAULT user | 角色 |
| preferences | JSON / JSONB | NOT NULL, DEFAULT {} | 偏好设置 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| last_login | TIMESTAMPTZ | NULL | 上次登录 |

**MVP 是否改动**
- 可不改表结构
- 若迁移成本可控，建议 `preferences` 从 `JSON` 换成 `JSONB`

---

## 1.2 `books`（MVP 重点改造）

> 当前模型：`backend/app/models/book.py:25-52`

### 保留字段
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| title | VARCHAR(512) | 书名 |
| subtitle | VARCHAR(512) | 副标题 |
| author | VARCHAR(255) | 作者 |
| publisher | VARCHAR(255) | 出版社 |
| publish_date | DATE / TIMESTAMPTZ | 出版日期 |
| isbn | VARCHAR(32) | ISBN |
| description | TEXT | 简介 |
| cover_url | TEXT | 封面路径/URL |
| file_path | TEXT | 本地文件路径 |
| file_format | ENUM(pdf,epub,mobi,azw3,txt,djvu) | 文件格式 |
| file_size | BIGINT | 文件大小 |
| language | VARCHAR(16) | 语言 |
| page_count | INTEGER | 页数 |
| rating | FLOAT | 评分 |
| rating_count | INTEGER | 评分人数 |
| tags | JSON / JSONB | 标签 |
| book_metadata | JSON / JSONB | 扩展元数据 |
| indexed_at | TIMESTAMPTZ | 入库时间 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### MVP 新增字段
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| content_hash | VARCHAR(128) | UNIQUE NULLABLE | 文件内容哈希 |
| hash_algorithm | VARCHAR(32) | NULL | 如 `sha256` |
| hash_status | ENUM(pending,done,failed,skipped) | NOT NULL DEFAULT pending | 哈希状态 |
| hash_error | TEXT | NULL | 哈希失败原因 |
| file_mtime | TIMESTAMPTZ | NULL | 文件修改时间 |
| source_provider | VARCHAR(32) | NULL | 最后一次元数据来源，如 `google_books` |
| metadata_synced_at | TIMESTAMPTZ | NULL | 最后一次同步元数据时间 |
| search_vector | TSVECTOR | INDEX(GIN) | PostgreSQL 全文检索向量 |

### MVP 索引建议
- `INDEX books_title_author_idx (title, author)`
- `INDEX books_content_hash_idx (content_hash)`
- `INDEX books_file_path_idx (file_path)`
- `GIN INDEX books_search_vector_idx (search_vector)`
- `GIN/TRGM INDEX books_title_trgm_idx (title)`
- `GIN/TRGM INDEX books_author_trgm_idx (author)`

### MVP 约束建议
- `UNIQUE (content_hash) WHERE content_hash IS NOT NULL`
- `UNIQUE (file_path)`

### 设计说明
- `file_path` 继续保留，避免 MVP 引入 `book_files` 大改造
- `content_hash` 成为主去重依据
- 同一本书换路径时，扫描逻辑应该根据 `content_hash` 找到旧记录并更新 `file_path`

---

## 1.3 `categories`（基本沿用）

> 当前模型：`backend/app/models/book.py:54-66`

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 分类 ID |
| name | VARCHAR(128) | UNIQUE, NOT NULL | 分类名 |
| parent_id | UUID | NULL, FK categories.id | 父分类 |
| description | TEXT | NULL | 描述 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

---

## 1.4 `book_categories`（沿用）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| book_id | UUID | PK, FK books.id | 图书 |
| category_id | UUID | PK, FK categories.id | 分类 |

---

## 1.5 `scan_jobs`（新增）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 任务 ID |
| job_type | ENUM(scan_directory,scan_file,rehash,resync_metadata) | NOT NULL | 任务类型 |
| status | ENUM(queued,running,completed,failed,partial_success,cancelled) | NOT NULL | 任务状态 |
| requested_path | TEXT | NOT NULL | 用户提交路径 |
| normalized_path | TEXT | NOT NULL | 规范化路径 |
| total_items | INTEGER | NOT NULL DEFAULT 0 | 总数 |
| processed_items | INTEGER | NOT NULL DEFAULT 0 | 已处理 |
| success_items | INTEGER | NOT NULL DEFAULT 0 | 成功 |
| failed_items | INTEGER | NOT NULL DEFAULT 0 | 失败 |
| skipped_items | INTEGER | NOT NULL DEFAULT 0 | 跳过 |
| error_message | TEXT | NULL | 任务级错误 |
| created_by | UUID | NULL, FK users.id | 操作人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| started_at | TIMESTAMPTZ | NULL | 开始时间 |
| finished_at | TIMESTAMPTZ | NULL | 结束时间 |

### 索引建议
- `INDEX scan_jobs_status_created_at_idx (status, created_at DESC)`
- `INDEX scan_jobs_created_by_idx (created_by)`

---

## 1.6 `scan_job_items`（新增）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 明细 ID |
| job_id | UUID | NOT NULL, FK scan_jobs.id ON DELETE CASCADE | 所属任务 |
| file_path | TEXT | NOT NULL | 当前处理文件路径 |
| file_format | VARCHAR(16) | NULL | 文件格式 |
| status | ENUM(queued,processing,created,updated,skipped,failed) | NOT NULL | 明细状态 |
| book_id | UUID | NULL, FK books.id | 命中的图书 |
| detected_hash | VARCHAR(128) | NULL | 计算出的 hash |
| error_message | TEXT | NULL | 错误信息 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

### 索引建议
- `INDEX scan_job_items_job_id_idx (job_id)`
- `INDEX scan_job_items_job_id_status_idx (job_id, status)`

---

## 1.7 `reading_progress`（MVP 精简增强）

> 当前模型：`backend/app/models/reading.py:17-37`

### 保留字段
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| user_id | UUID | 用户 |
| book_id | UUID | 图书 |
| current_page | INTEGER | 当前页 |
| total_pages | INTEGER | 总页数 |
| progress_percent | FLOAT | 进度百分比 |
| status | ENUM(not_started,reading,completed,abandoned) | 阅读状态 |
| started_at | TIMESTAMPTZ | 开始时间 |
| finished_at | TIMESTAMPTZ | 完成时间 |
| last_read_at | TIMESTAMPTZ | 最近阅读时间 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### MVP 调整
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| locator | JSONB | NULL | 统一阅读定位信息 |
| notes | TEXT | NULL, legacy | 不作为主接口字段，后续废弃 |
| bookmarks | JSONB / JSON | NULL, legacy | 不作为主接口字段，后续废弃 |

### 新约束
- `UNIQUE (user_id, book_id)`

### locator 示例
- PDF：`{"type":"pdf_page","page":12,"offset":0.35}`
- EPUB：`{"type":"epub_cfi","cfi":"epubcfi(...)"}`
- TXT：`{"type":"text_offset","start":1234,"end":1301}`

---

## 1.8 `book_notes`（MVP 新增，承接“做笔记”需求）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 笔记 ID |
| user_id | UUID | NOT NULL, FK users.id | 用户 |
| book_id | UUID | NOT NULL, FK books.id | 图书 |
| locator | JSONB | NULL | 可选阅读位置 |
| note_text | TEXT | NOT NULL | 笔记内容 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

### 索引建议
- `INDEX book_notes_user_book_idx (user_id, book_id, updated_at DESC)`
- 可选：`GIN INDEX book_notes_locator_idx (locator)`

### 设计说明
- MVP 先支持“自由文本笔记 + 可选定位”
- 不做高亮颜色、摘录范围、批注 thread
- Phase 2 再升级为 `annotations` / `bookmarks`

---

## 2. MVP API 清单

## 2.1 API 设计原则
- **尽量复用现有路由风格**，降低后端改造成本
- 对前端只暴露 MVP 必需接口
- Admin 不单独搞 BFF，直接调用后端 API

---

## 2.2 Auth

> 当前基础：`backend/app/api/auth.py:10-61`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | 公共 | 保留 | 用户注册 |
| POST | `/api/v1/auth/login` | 公共 | 保留 | 登录拿 JWT |
| GET | `/api/v1/auth/me` | 用户 | 保留 | 当前用户信息 |

---

## 2.3 Books

> 当前基础：`backend/app/api/books.py:14-112`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/books` | 用户 | 修改 | 图书列表 + 搜索 + 过滤 + 分页 |
| GET | `/api/v1/books/{book_id}` | 用户 | 保留 | 图书详情 |
| POST | `/api/v1/books` | 管理员 | 保留 | 手动创建图书 |
| PUT | `/api/v1/books/{book_id}` | 管理员 | 保留 | 编辑图书 |
| DELETE | `/api/v1/books/{book_id}` | 管理员 | 保留 | 删除图书 |
| POST | `/api/v1/books/{book_id}/metadata-sync` | 管理员 | 新增/迁移 | 同步外部元数据 |
| POST | `/api/v1/books/{book_id}/extract-cover` | 管理员 | 新增/迁移 | 提取/更新封面 |

### `GET /books` 建议查询参数
| 参数 | 类型 | 说明 |
|---|---|---|
| page | int | 页码 |
| page_size | int | 每页数量 |
| q | string | 搜索词 |
| author | string | 作者过滤 |
| category_id | uuid | 分类过滤 |
| format | string | 文件格式过滤 |
| sort | string | `updated_at` / `title` / `rating` |
| order | string | `asc` / `desc` |

### `GET /books` 返回建议
```json
{
  "items": [],
  "total": 123,
  "page": 1,
  "page_size": 20
}
```

---

## 2.4 Scanner Jobs

> 当前基础：`backend/app/api/scanner.py:42-234`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| POST | `/api/v1/scanner/jobs/directory` | 管理员 | 新增 | 创建目录扫描任务 |
| POST | `/api/v1/scanner/jobs/file` | 管理员 | 新增 | 创建单文件扫描任务 |
| GET | `/api/v1/scanner/jobs` | 管理员 | 新增 | 任务列表 |
| GET | `/api/v1/scanner/jobs/{job_id}` | 管理员 | 新增 | 任务详情 |
| GET | `/api/v1/scanner/jobs/{job_id}/items` | 管理员 | 新增 | 任务明细 |
| POST | `/api/v1/scanner/jobs/{job_id}/retry-failed` | 管理员 | 新增 | 重试失败项 |

### `POST /scanner/jobs/directory` 请求示例
```json
{
  "directory": "/data/books"
}
```

### `POST /scanner/jobs/directory` 返回示例
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Directory scan queued"
}
```

### `GET /scanner/jobs/{job_id}` 返回示例
```json
{
  "id": "uuid",
  "job_type": "scan_directory",
  "status": "running",
  "requested_path": "/data/books",
  "total_items": 1000,
  "processed_items": 420,
  "success_items": 390,
  "failed_items": 12,
  "skipped_items": 18,
  "started_at": "...",
  "finished_at": null
}
```

---

## 2.5 Categories

> 当前基础：`backend/app/api/categories.py:12-164`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/categories` | 用户 | 保留 | 分类列表 |
| GET | `/api/v1/categories/{category_id}` | 用户 | 保留 | 分类详情 |
| POST | `/api/v1/categories` | 管理员 | 保留 | 创建分类 |
| DELETE | `/api/v1/categories/{category_id}` | 管理员 | 保留 | 删除分类 |
| GET | `/api/v1/categories/{category_id}/books` | 用户 | 保留 | 分类下图书 |
| POST | `/api/v1/categories/{category_id}/books/{book_id}` | 管理员 | 保留 | 图书加分类 |
| DELETE | `/api/v1/categories/{category_id}/books/{book_id}` | 管理员 | 保留 | 图书移出分类 |

---

## 2.6 Reading Progress

> 当前仅有模型，无完整 API：`backend/app/models/reading.py:17-37`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/reading-progress/{book_id}` | 用户 | 新增 | 获取当前用户该书阅读进度 |
| PUT | `/api/v1/reading-progress/{book_id}` | 用户 | 新增 | 更新阅读进度 |
| GET | `/api/v1/reading-progress/recent` | 用户 | 新增 | 最近阅读列表 |

### `PUT /reading-progress/{book_id}` 请求示例
```json
{
  "status": "reading",
  "progress_percent": 42.5,
  "current_page": 120,
  "total_pages": 300,
  "locator": {
    "type": "pdf_page",
    "page": 120,
    "offset": 0.18
  }
}
```

---

## 2.7 Book Notes（MVP 笔记）

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/books/{book_id}/notes` | 用户 | 新增 | 当前用户该书笔记列表 |
| POST | `/api/v1/books/{book_id}/notes` | 用户 | 新增 | 创建笔记 |
| PUT | `/api/v1/books/{book_id}/notes/{note_id}` | 用户 | 新增 | 编辑笔记 |
| DELETE | `/api/v1/books/{book_id}/notes/{note_id}` | 用户 | 新增 | 删除笔记 |

### `POST /books/{book_id}/notes` 请求示例
```json
{
  "locator": {
    "type": "epub_cfi",
    "cfi": "epubcfi(...)"
  },
  "note_text": "这里讲的观点值得后续整理。"
}
```

---

## 2.8 Files

> 当前基础：`backend/app/api/files.py:14-125`

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/files/download/{book_id}` | 用户 | 保留 | 下载图书 |
| GET | `/api/v1/files/stream/{book_id}` | 用户 | 修改 | 流式阅读，补 Range 支持 |
| GET | `/api/v1/files/cover/{book_id}` | 公共 | 保留 | 获取封面 |

---

## 2.9 Admin Dashboard（MVP 可选，但推荐）

| 方法 | 路径 | 权限 | 类型 | 说明 |
|---|---|---|---|---|
| GET | `/api/v1/admin/overview` | 管理员 | 新增 | 后台首页汇总统计 |

### 返回建议
```json
{
  "book_count": 10234,
  "category_count": 87,
  "scan_jobs_running": 1,
  "scan_jobs_failed": 3,
  "recent_added_books": 20
}
```

---

## 3. MVP API 最终建议清单（按实现优先级）

### 第一批必须做
1. `POST /scanner/jobs/directory`
2. `GET /scanner/jobs/{job_id}`
3. `GET /books`
4. `GET /books/{book_id}`
5. `PUT /reading-progress/{book_id}`
6. `GET /reading-progress/{book_id}`
7. `GET /files/stream/{book_id}`
8. `GET /files/download/{book_id}`

### 第二批建议做
9. `GET /scanner/jobs`
10. `GET /scanner/jobs/{job_id}/items`
11. `POST /books/{book_id}/metadata-sync`
12. `POST /books/{book_id}/extract-cover`
13. `GET /books/{book_id}/notes`
14. `POST /books/{book_id}/notes`
15. `PUT /books/{book_id}/notes/{note_id}`
16. `DELETE /books/{book_id}/notes/{note_id}`
17. `GET /admin/overview`

---

## 4. 与当前代码的最关键差异

1. 当前扫描入口：`backend/app/api/scanner.py:42-56`
   - **现状**：直接 `BackgroundTasks`
   - **MVP**：改成 `scan_jobs + Celery`

2. 当前去重逻辑：`backend/app/services/scanner_service.py:72-77`
   - **现状**：`file_path + file_size`
   - **MVP**：改成 `content_hash`

3. 当前搜索逻辑：`backend/app/api/books.py:25-32`
   - **现状**：`ILIKE`
   - **MVP**：改成 PostgreSQL FTS

4. 当前阅读进度模型：`backend/app/models/reading.py:17-37`
   - **现状**：只有粗粒度字段
   - **MVP**：增加 `locator`、唯一约束、独立 `book_notes`

---

## 5. 实施建议（从后端角度）

### Step 1
先做 Alembic 迁移：
- `books` 增字段
- `scan_jobs`
- `scan_job_items`
- `reading_progress` 增约束与 `locator`
- `book_notes`

### Step 2
接 Celery，把 `scan-directory` 改为 job 创建接口

### Step 3
把 `GET /books` 换成 PostgreSQL FTS

### Step 4
补 `reading-progress` + `book_notes` API

### Step 5
最后再接 Admin Web / Reader Web

---

## 6. 结论

如果按这个 MVP 草案实施：
- 可以满足 **hash 入库、CRUD、搜索、下载、Web 阅读、基础做笔记、Docker/VPS 部署**
- 也不会在第一阶段就被“多文件归一、一书多格式、高亮系统、复杂同步冲突”拖慢

Phase 2 再继续补：
- `book_files`
- `bookmarks`
- `annotations`
- Capacitor / Tauri 封装
- Meilisearch
